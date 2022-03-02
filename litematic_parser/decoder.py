import math
import re
import time

import nbtlib as nbt
import numpy as np

def nbt_to_python(value):
    # 0 IQ method bcos I want quick universal convert
    match type(value):
        case nbt.tag.Byte, nbt.tag.Int, nbt.tag.Short, nbt.tag.Long:
            return int(value)
        case nbt.tag.Float, nbt.tag.Double:
            return float(value)
        case nbt.tag.String:
            return str(value)
        case nbt.tag.ByteArray, nbt.tag.IntArray, nbt.tag.LongArray:
            return np.ndarray(value)
        case nbt.tag.List:
            return list(value)
        case nbt.tag.Compound:
            return dict(value)

def snake_case(text):
    return '_'.join([k.lower() for k in re.split('(?=[A-Z])\B', text)])

class Schematic:
    def __init__(self, file: str):
        self.file = file
        self.file_format = self.get_file_format()
        with open(self.file, 'rb') as f:
            self.nbt = nbt.File.load(f, gzipped=True)
        self.metadata = self.get_metadata()
        self.data_version = self.nbt['MinecraftDataVersion']
        self.version = self.nbt['Version']

        self.regions = {}
        for i, v in self.nbt['Regions'].items():
            self.regions[i] = Region(v)

    def get_file_format(self):
        format = re.search('((?!\.)[^.]+)$', self.file).group()
        match format:
            case 'litematic':
                return format
            case _:
                raise ValueError('File format not supported')

    def get_metadata(self):
        mdata = self.nbt['Metadata']
        format_mdata = {}
        for i, v in mdata.items():
            format_mdata[snake_case(i)] = v
        return format_mdata


class Region:
    times = []
    def __init__(self, data: nbt.tag.Compound):
        self.nbt = data
        self.dimensions = tuple(abs(int(i)) for i in self.nbt['Size'].values())
        self.volume = np.product(self.dimensions)
        self.bit_width = int.bit_length(len(self.nbt['BlockStatePalette']) - 1)

    def get_block_state(self, index):
        start = time.time()
        start_offset = index * self.bit_width
        start_arr_index = start_offset >> 6
        end_arr_index = ((index + 1) * self.bit_width - 1) >> 6
        start_bit_offset = start_offset & 0x3F
        shift = nbt.Long((1 << self.bit_width) - 1)

        if start_arr_index == end_arr_index:
            index = self.nbt['BlockStates'][start_arr_index] >> start_bit_offset & shift
        else:
            end_offset = 64 - start_bit_offset
            index = (abs(self.nbt['BlockStates'][start_arr_index] >> start_bit_offset) | self.nbt['BlockStates'][end_arr_index] << end_offset) & shift

        end = time.time()
        self.times.append(end-start)

        return index

