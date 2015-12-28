house_code = {
              'A': 0b0110,
              'C': 0b0010,
              'B': 0b1110,
              'E': 0b0001,
              'D': 0b1010,
              'G': 0b0101,
              'F': 0b1001,
              'I': 0b0111,
              'H': 0b1101,
              'K': 0b0011,
              'J': 0b1111,
              'M': 0b0000,
              'L': 0b1011,
              'O': 0b0100,
              'N': 0b1000,
              'P': 0b1100
             }

device_code = [
               None,
               0b0110,
               0b1110,
               0b0010,
               0b1010,
               0b0001,
               0b1001,
               0b0101,
               0b1101,
               0b0111,
               0b1111,
               0b0011,
               0b1011,
               0b0000,
               0b1000,
               0b0100,
               0b1100
              ]

function_code = {
                 "ALL OFF": 0b0000,
                 "ALL LIGHTS ON": 0b0001,
                 "ON": 0b0010,
                 "OFF": 0b0011,
                 "DIM": 0b0100,
                 "BRIGHT": 0b0101,
                 "ALL LIGHTS OFF": 0b0110,
                 "PRESET DIM 1": 0b1010,
                 "PRESET DIM 2": 0b1011,
                 "STATUS OFF": 0b1110,
                 "EXTENDED DATA TRANSFER": 0b1100,
                 "EXTENDED CODE": 0b0111
                }

# Construct the inverses of above
code_house = {}
for key, val in house_code.items():
    code_house[val] = key

code_function = {}
for key, val in function_code.items():
    code_function[val] = key
