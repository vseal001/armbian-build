#!/bin/bash
# KC2 / K10Plus IR diagnostic - run as root ON THE BOX:
#   curl -sL https://raw.githubusercontent.com/vseal001/armbian-build/main/custom-model/tools/ir_diag.sh | bash
echo "== kernel =="
uname -a
echo; echo "== rc devices =="
ls -l /sys/class/rc/ 2>&1
echo; echo "== dmesg IR lines =="
dmesg | grep -iE "gpio-ir|rc.core|lirc|ir-receiver" | head -30
echo; echo "== ir-keytable present? =="
command -v ir-keytable || echo "ir-keytable NOT installed"
ir-keytable 2>&1 | head -20
echo; echo "== udev rule =="
cat /etc/udev/rules.d/99-kc2-ir-keymap.rules 2>&1
echo; echo "== keymap file =="
ls -l /etc/rc_keymaps/ 2>&1
echo; echo "== loaded modules =="
lsmod | grep -E "gpio_ir|ir_nec|rc_core|lirc" || echo "(no ir modules loaded)"
echo; echo "== kernel config =="
grep -E "CONFIG_IR_GPIO_CIR|CONFIG_IR_NEC_DECODER|CONFIG_RC_CORE" /boot/config-$(uname -r) 2>/dev/null || zcat /proc/config.gz 2>/dev/null | grep -E "CONFIG_IR_GPIO_CIR|CONFIG_IR_NEC_DECODER|CONFIG_RC_CORE"
echo; echo "== 15s capture: PRESS REMOTE KEYS NOW =="
timeout 15 ir-keytable -t 2>&1 | head -50
echo "== capture done =="
