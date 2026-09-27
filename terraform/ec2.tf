data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023*-x86_64"]
  }

  filter {
    name   = "state"
    values = ["available"]
  }
}

resource "aws_instance" "workload" {
  ami                         = data.aws_ami.amazon_linux.id
  instance_type               = var.ec2_instance_type
  subnet_id                   = aws_subnet.public_a.id
  vpc_security_group_ids      = [aws_security_group.ec2.id]
  associate_public_ip_address = true

  iam_instance_profile = aws_iam_instance_profile.ec2_workload.name

  monitoring = true

  user_data = <<-EOF
#!/bin/bash
set -e

dnf update -y

dnf install -y \
  postgresql17 \
  jq \
  awscli \
  stress-ng \
  amazon-cloudwatch-agent

systemctl enable amazon-ssm-agent
systemctl start amazon-ssm-agent

systemctl enable amazon-cloudwatch-agent

cat > /opt/cloud-cost-db-workload.sh <<'SCRIPT'
#!/bin/bash

set -e

export PGHOST="${aws_db_instance.workload.address}"
export PGPORT="${aws_db_instance.workload.port}"

SECRET_JSON=$(aws secretsmanager get-secret-value \
  --secret-id "${aws_secretsmanager_secret.rds_credentials.arn}" \
  --region "${var.aws_region}" \
  --query SecretString \
  --output text)

export PGUSER=$(echo "$SECRET_JSON" | jq -r '.username')
export PGPASSWORD=$(echo "$SECRET_JSON" | jq -r '.password')
export PGDATABASE=$(echo "$SECRET_JSON" | jq -r '.database')

psql -c "
CREATE TABLE IF NOT EXISTS workload_events (
    id BIGSERIAL PRIMARY KEY,
    workload_type VARCHAR(50),
    payload_size INTEGER,
    sequence_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"

psql -c "
INSERT INTO workload_events
    (workload_type, payload_size, sequence_id)
SELECT
    'baseline',
    1024,
    generate_series
FROM generate_series(1, 500);
"

psql -c "
SELECT COUNT(*) AS total_events
FROM workload_events;
"
SCRIPT

chmod +x /opt/cloud-cost-db-workload.sh

cat > /etc/systemd/system/cloud-cost-db-workload.service <<'SERVICE'
[Unit]
Description=Cloud Cost Optimization PostgreSQL Workload
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/opt/cloud-cost-db-workload.sh
RemainAfterExit=no

[Install]
WantedBy=multi-user.target
SERVICE

cat > /opt/cloud-cost-cpu-workload.sh <<'SCRIPT'
#!/bin/bash

set -e

echo "Starting controlled CPU workload"

stress-ng \
  --cpu 2 \
  --cpu-load 80 \
  --timeout 10m

echo "CPU workload completed"
SCRIPT

chmod +x /opt/cloud-cost-cpu-workload.sh

cat > /etc/systemd/system/cloud-cost-cpu-workload.service <<'SERVICE'
[Unit]
Description=Cloud Cost Optimization CPU Workload

[Service]
Type=oneshot
ExecStart=/opt/cloud-cost-cpu-workload.sh
RemainAfterExit=no

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload

systemctl enable cloud-cost-db-workload.service
systemctl enable cloud-cost-cpu-workload.service

cat > /opt/aws-cloudwatch-agent.json <<'CWCONFIG'
{
  "agent": {
    "metrics_collection_interval": 60,
    "run_as_user": "root"
  },
  "metrics": {
    "namespace": "CloudCostOptimization",
    "metrics_collected": {
      "disk": {
        "measurement": [
          "used_percent"
        ],
        "metrics_collection_interval": 60,
        "resources": [
          "*"
        ]
      },
      "mem": {
        "measurement": [
          "mem_used_percent"
        ],
        "metrics_collection_interval": 60
      },
      "swap": {
        "measurement": [
          "swap_used_percent"
        ],
        "metrics_collection_interval": 60
      }
    }
  }
}
CWCONFIG

/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -c file:/opt/aws-cloudwatch-agent.json \
  -s || true

echo "Cloud Cost Optimization workload initialization complete"
echo "Experiment services installed and ready for controlled execution."
EOF

  tags = {
    Name       = "${var.project_name}-workload-ec2"
    Workload   = "Controlled-Cost-Experiment"
    DataSource = "AWS"
    Experiment = "EC2-RDS-Lambda"
  }

  depends_on = [
    aws_db_instance.workload,
    aws_iam_role_policy.ec2_rds_secret_access
  ]
}

output "ec2_instance_id" {
  description = "EC2 workload instance ID"
  value       = aws_instance.workload.id
}

output "ec2_private_ip" {
  description = "EC2 private IP"
  value       = aws_instance.workload.private_ip
}

output "ec2_public_ip" {
  description = "EC2 public IP"
  value       = aws_instance.workload.public_ip
}

output "ec2_instance_type" {
  description = "EC2 instance type"
  value       = aws_instance.workload.instance_type
}