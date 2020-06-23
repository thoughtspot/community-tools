# IAM Instance Profile
resource "aws_iam_instance_profile" "default" {
  name = local.iam_name
  role = aws_iam_role.default.name
  path = var.iam_path
}

resource "aws_iam_role" "default" {
  name               = local.iam_name
  assume_role_policy = data.aws_iam_policy_document.assume_role_policy.json
  path               = var.iam_path
  description        = var.description
  tags               = merge({ "Name" = local.iam_name }, var.tags)
}

data "aws_iam_policy_document" "assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_policy" "default" {
  name        = local.iam_name
  policy      = local.iam_policy
  path        = var.iam_path
  description = var.description
}

resource "aws_iam_role_policy_attachment" "default" {
  role       = aws_iam_role.default.name
  policy_arn = aws_iam_policy.default.arn
}

locals {
  iam_name   = "${var.name}-session-manager"
  iam_policy = var.iam_policy == "" ? data.aws_iam_policy.default.policy : var.iam_policy
}

data "aws_iam_policy" "default" {
  arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2RoleforSSM"
}
