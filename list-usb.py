import usb.core

dev = usb.core.find(find_all=True)

for cfg in dev:
    print(cfg)
    print("device bus:", cfg.bus)
    print("device address:", cfg.address)
    print("device port:", cfg.port_number)
    print("device speed:", cfg.speed)