data "aws_iam_policy_document" "s3_access_policy" {
	/*
    Creates a json document specifying the policy to be used as per aws conventions
    	- restrict access to the specifc S3 bucket
  */
	statement {
    actions = [
      "s3:*"
    ]
    effect = "Allow"
    resources = [
      "arn:aws:s3:::${var.bucket_name}",
      "arn:aws:s3:::${var.bucket_name}/*",
    ]
	}
}

resource "aws_iam_role" "ec2_s3_access_role" {
  name = "${var.cluster_name}_ec2_s3_access_role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF

  tags = {
      tag-key = "${var.cluster_name}"
  }
}

resource "aws_iam_instance_profile" "ec2_s3_profile" {
  name = "${var.cluster_name}_ec2_s3_profile"
  role = "${aws_iam_role.ec2_s3_access_role.name}"
}

resource "aws_iam_role_policy" "ec2_s3_policy" {
  name              = "${var.cluster_name}_ec2_s3_policy"
  role              = "${aws_iam_role.ec2_s3_access_role.id}"

  policy            = "${data.aws_iam_policy_document.s3_access_policy.json}"
}

output "ec2_s3_iam_profile" {
    description       = "The name of the s3-ec2 iam profile"
    value             = "${aws_iam_instance_profile.ec2_s3_profile.name}"
}
