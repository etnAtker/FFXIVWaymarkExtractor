import json
import struct
from datetime import datetime


class WaymarkPreset:
    WM_KEYS = ['A', 'B', 'C', 'D', 'One', 'Two', 'Three', 'Four']

    def __init__(self, preset: int = None):
        self.waymarks = []
        self.zone = 0
        self.name = f'Preset {preset}' if preset is not None else 'Imported'

    def append(self, x: float, y: float, z: float):
        idx = len(self.waymarks)

        if idx >= 8:
            raise RuntimeError(f'Waymark index out of range: {idx}')

        self.waymarks.append(Waymark(x, y, z, idx))

    def set_wm_info(self, enabled: int, zone: int):
        for idx, waymark in enumerate(self.waymarks):
            active = ((1 << idx) & enabled) != 0
            waymark.active = active

        self.zone = zone

    def to_json(self) -> str:
        j = {
            'Name': self.name,
            'MapID': self.zone,
        }
        for idx, waymark in enumerate(self.waymarks):
            j[WaymarkPreset.WM_KEYS[idx]] = waymark.to_dict()

        return json.dumps(j, separators=(',', ':'))


class Waymark:
    def __init__(self, x: float, y: float, z: float, idx: int, active: bool = True):
        self.x = x
        self.y = y
        self.z = z
        self.id = idx
        self.active = active

    def to_dict(self):
        return {
            'X': self.x,
            'Y': self.y,
            'Z': self.z,
            'ID': self.id,
            'Active': self.active,
        }



def xor0x31(bs: bytes) -> bytes:
    return bytes(map(lambda x: x ^ 0x31, bs))


def main():
    with open('UISAVE.DAT', 'rb') as f:
        data = f.read()

    p = 16 + 16  # header + character_id
    wm_presets = []

    while p < len(data):
        header = xor0x31(data[p:p + 16])
        ind, _, _, _, size, _, _ = struct.unpack('<HHHHIHH', header)

        p += 16  # section header

        # section 0x11: FMARKER(https://github.com/aers/FFXIVClientStructs/blob/main/FFXIVClientStructs/FFXIV/Client/UI/Misc/UiSavePackModule.cs)
        if ind == 0x11:
            print(f'Reading FMARKER, {size} bytes long.')
            wm_data = xor0x31(data[p:p + size])
            wm_p = 16 # the first 16 bytes are unknown

            # there are 30 presets, (12 * 8 + 8) * 30 = 3120 bytes long
            for preset in range(30):
                print(f'Preset #{preset + 1}')
                wm_preset = WaymarkPreset(preset + 1)
                for marker in ['A', 'B', 'C', 'D', '1', '2', '3', '4']:
                    x, y, z = struct.unpack('<iii', wm_data[wm_p:wm_p+12])
                    wm_p += 12
                    print(f'{marker}: ({x / 1000}, {y / 1000}, {z / 1000})')
                    wm_preset.append(x / 1000, y / 1000, z / 1000)

                enabled, res, zone, ts = struct.unpack('<BBHI', wm_data[wm_p:wm_p + 8])
                wm_p += 8
                print(f'Enabled Bitmask: {enabled}; '
                      f'Zone ID: {zone}; '
                      f'Created At: {datetime.fromtimestamp(ts)}\n')

                if enabled != 0:
                    wm_preset.set_wm_info(enabled, zone)
                    wm_presets.append(wm_preset)

            # the last 4 bytes are unknown

        p += size + 4  # data + trailing

    print(f'{len(wm_presets)} presets are extracted:')
    for wm_preset in wm_presets:
        print(wm_preset.to_json())


if __name__ == '__main__':
    main()