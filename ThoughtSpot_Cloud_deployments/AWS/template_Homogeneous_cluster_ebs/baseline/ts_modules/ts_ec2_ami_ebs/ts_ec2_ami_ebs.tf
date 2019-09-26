
resource "aws_instance" "ts-aws-instance" {
  count                       = "${var.number_of_instances}"
  ami                         = "${var.base_ami}"
  instance_type               = "${var.ts_instance_type}"
  monitoring                  = false
  subnet_id                   = "${var.vpc_subnet_id}"
  vpc_security_group_ids      = "${var.security_groups}"

  tags = {
        Name                  = "${var.customer_name}-${count.index + 1}"
  }
}

output "ts_host_ip" {
    value = "${aws_instance.ts-aws-instance.*.private_ip}"
}

output "ts_inst_id" {
    value = "${aws_instance.ts-aws-instance.*.id}"
}
