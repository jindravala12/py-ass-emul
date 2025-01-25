from data import *
from disassembler import *
import re


def get_byteslength(instruction, args):
    # 3 možnosti:
    # - Immutable
    # - Register
    # - Memmory
    #
    # Size:
    # byte/word/(none)
    #
    # Taky potřebuju vědět:
    # Který opcode

    output = Instruction()

    output.operation = "MOV"  # - TODO: extract from line
    output.size = 2  # Vyčíst z idk

    ...


def deprecated__parse_param(par: str) -> 'Parameter':  # Part of assembler
    """
    ! Work in progress. Yet can't handle labels nor math např.: [label + 2]
    ? Perhaps regex would be usefull??
    pls help
    """
    # Register
    if par in REGISTERS:
        return Register(par)
    
    if "\"" in par or "'" in par:
        raise Exception("Strings are not supported")


    if "FAR" in par:
        # TODO: Handle 
        ... 

    try:# Immutable    
        return Immutable(parse_number(par))
    except:
        pass

    # Memmory
    if par[0] == '[' and par[-1] == "]":
        par = par[1:-1]
        a = Memmory(None, None)
        for r in MOD_00_RM:
            if r in par:
                a.source = r
                par = par.replace(r + '+', "+")
                break
        else:
            raise Exception("Nebyl rozpoznán segment")

        if par[0] == "+":
            par = par.replace('+', '')
            # If is not ok, it's the users problem.
            a.displacement = parse_number(par)

        return a

    # Pointer
    if "PTR" in par:
        par.replace("PTR", "", 1)  # Hope not
        par.replace("FAR", "", 1)
        return Label(par, include_segment=True)

    raise Exception(f"Nebylo možné zpracovat parametr {par}")

def parse_param_02(template: str, arg: str) -> 'Parameter':
    # ? Je tato funkce vůbec k něčemu??
    if template in SEG_REGS:
        
        return Register(arg)

    ...


def assemble(code: str) -> list[int]:
    labels = {}
    byte_length = 0  # TODO: rename

    templates = []
    segments_templates = []

    for i, line in enumerate(code.split("\n")):
        line = re.sub(r'\s+', ' ', line)  # Make all whitespace one space

        if line.strip() == "":
            continue

        if line.startswith("segment"):
            segment = line.split(" ")[1]
            labels[segment] = i
            segments_templates.append([])
            continue

        label, instr, args = parse_line_parts(line)

        size = get_instruction_size(instr, args)

        if label != "":
            labels[label] = byte_length

        if instr+str(size) not in INSTRUCTIONS_v2:
            raise Exception(f"Unknown instruction {instr}")

        possible_codes = INSTRUCTIONS_v2[instr+str(size)]

        for instr_params, info in possible_codes:
            if matches_args(instr_params.split(" "), args):
                segments_templates[-1].append((instr_params, args, info))
                break
        else:
            raise Exception(f"Invalid arguments for instruction {instr}")

        byte_length += info["expected_length"]

    bytecode = []

    for templates in segments_templates:
        segment_bytecode = []
        for params, args, info in templates:
            bytes = convert_to_bytes(args, params, info, labels, len(bytecode))

            if len(bytes) != info["expected_length"]:
                # 844 - random number, kdybych někde jinde přidával stejnou message
                raise Exception(f"Chyba emulátoru. Prosím napiš na Diskusní fórum úlohy. (ErrCode: 844 - neočekávaný počet bajtů)") 
            
            segment_bytecode.extend(bytes)
        

        # TODO: Doplnit None do nějakého násobku 2 nebo tak??
        segment_bytecode.extend([None for _ in range(42)])
        bytecode.extend(segment_bytecode)

    return bytecode




def parse_line_parts(line: str) -> tuple[str, str, list[str]]:
    label, line = line.split(" ", 1)  # If no label, empty string
    instr, line = split_on(line, " ")
    # regex to split by ';' but ignore semicolons within strings
    # line = re.split(r'(?<!");', line, 1)[0]
    line, _ = split_on(line, ";")

    args = [l.strip() for l in line.split(",")]

    return label, instr, args

def split_on(line: str, char: str) -> tuple[str, str]:
    return line.split(char, 1) if char in line else (line, "")

# print(parse_line_parts(" HLT"))

def get_instruction_size(instruction: str, args: list[str]) -> int:
    """Returns 0/8/16"""
    if instruction in INSTRUCTIONS_WITHOUT_PARAMETER:
        return 0
    
    if instruction == "INT": # Hnusný hardcode, ale zjistil jsem to pozdě
        return 0 if args[0] == "3" else 8
    
    if instruction in ["JMP", "CALL"]:
        if "SHORT" in args[0]:
            return 8
        if "FAR" in args[0]:
            return 32
        return 16

    if instruction[0] == "J":
        # JZ, JNZ, ...
        return 8

    if args == []:
        return 0

    size = None

    for i, arg in enumerate(args):
        figured = None
        if "byte " in arg.lower():
            figured = 8
            args[i] = arg.replace("byte ", "")
        elif "word " in arg.lower():
            figured = 16
            args[i] = arg.replace("word ", "")

        elif arg in RM_8_REGS:
            figured = 8
        elif arg in RM_16_REGS or arg in SEG_REGS:
            figured = 16

        if size is None:
            size = figured

        if figured is not None and size != figured:
            raise Exception("Incompatible sizes of arguments")

    if size is None:
        raise Exception("No size specified")

    return size


def matches_args(templates: list[str], args: list[str]):
    assert len(templates) == len(args), "Nevalidní počet argumentů"

    for i in range(len(templates)):
        templ, arg = templates[i], args[i].strip()

        if templ == "":
            continue

        if templ in ["1", "3"]:
            if arg != templ:
                return False
            continue

        # TODO: Tohle vypadá tak strašně. Acho jo. Musím to přepsat
        if arg in SEG_REGS:
            if templ not in SEG_REGS or templ[0] != "S":
                return False
            continue

        if arg in REGISTERS:
            # Is a general register:
            if templ[0] not in ["G", "E"] and templ not in REGISTERS:
                return False
            continue

        if "[" in arg and "]" in arg:
            # Is a memmory:
            if templ[0] not in ["G", "E"]:
                return False
            continue

        # Is an immediate:
        if templ[0] not in ["I", "J", "A"]:
            return False

    return True


# print(matches_args(["Ib"], ["42"]))
# print(matches_args(["Ev"], ["BX"]))
# print(matches_args(["Ev"], ["42"]))
# print(matches_args(["Ev"], ["[42]"]))
# print(matches_args(["Ev"], ["[BX+42]"]))
# print(matches_args(["Gb"], ["AL"]))
# print(matches_args(["Gb"], ["SS"]))
# print(matches_args(["Gb"], ["34"]))

# print("OK")

Template = dict[str, None | int | list[int]]

def convert_to_bytes(args: list[str], parameters: str, info: Template, 
                     labels: dict[str, int], # Hej už se to tu dost množí argumenty - chtělo by to přepracovat :-(
                     curr_instr_idx: int # TODO: Lepší název
                     ) -> list[int]:
    # ! NOT TESTED !
    output = []

    # --- 1) Vyplnit celé info
    info["data"] = []
    # Prefixes
    for prefix in PREFIXES:
        for i, arg in enumerate(args):
            if prefix in arg:
                args[i] = arg.replace(prefix, "")
                if prefix in info and info[prefix] is not None:
                    raise Exception("Can't have two prefixes or sth - problem")
                info["prefix"] = PREFIX_CODES[prefix]

    # Parse args
    for i, param in enumerate(parameters.split(" ")):
        arg = args[i]

        if param == "":
            continue

        if param in REGISTERS:
            # Encoded in opcode, no more details needed
            continue

        match param[0]:
            case "A":
                if ":" in arg:
                    seg, off = [p.strip() for p in arg.split(":")]
                    output.extend(int_to_bytes(calculate_value(off, labels), 16))
                    output.extend(int_to_bytes(calculate_value(seg, labels), 16))
                    
            case "J":
                # Relative offset
                # Calculate distance, assert distance < 2**x
                desitny = calculate_value(arg, labels)
                dist = desitny - curr_instr_idx
                size = 8 if param[1] == "b" else 16
                convert_to_bytes(dist, size)
                info["data"].extend(dist)

            case "I":
                val = calculate_value(arg, labels)
                size = 8 if param[1] == "b" else 16
                info["data"].extend(int_to_bytes(val, size))

            case "G":
                reg_val = 0
                if arg[1] == "b":
                    reg_val = RM_8_REGS.index(arg)
                else:
                    reg_val = RM_16_REGS.index(arg) 

                if "modrm" not in info:
                    info["modrm"] = 0

                info["modrm"] += reg_val *8  # Reg part of modrm

            case "E":
                if "modrm" not in info: # Code duplicity
                    info["modrm"] = 0

                rm_val, mod_val = 0, 0
                if arg[0] == "[" and arg[-1] == "]":
                    # Assert arg is without prefix
                    arg = arg[1:-1]

                    for i, regref in enumerate(MOD_00_RM):
                        if regref in arg:
                            rm_val = i
                            arg = arg.replace(regref, "")
                            break
                    else:
                        rm_val = 6 # Only displacement - protože prostě někdo si řelk, jo, tohle je dobrý nápad. viz tabulka

                    displ = calculate_value(arg, labels)
                    size = 0
                    if displ != 0:
                        size = 8 if displ < 2**8 else 16
                        info["data"].extend(displ, size)
                        mod_val = size // 8

                else:
                    mod_val = 3  # Selects register 
                    if arg[1] == "b":
                        rm_val = RM_8_REGS.index(arg)
                    else:
                        rm_val = RM_16_REGS.index(arg)

                info["modrm"] += rm_val
                info["modrm"] += mod_val * 64

                
            case "S":
                # Segment register
                reg_val = SEG_REGS.index(arg)
                info["modrm"] += reg_val * 8
                # ? Snad je to správně

    if "E" in "".join(parameters):
        to_fill = info["expected_length"] - 1 - (1 if "prefix" in info else 0) - (1 if "modrm" in info else 0)
        info["data"].extend([0x90] * to_fill)
    # 1) Register / Memmory (=> ModR/M + možný displacement - taky podle toho upravid Mod) 
    # 2) Ap (pointer) -> uložit segment a offset
    # 3) I (immediate) -> uložit hodnotu


    # --- 2) Předělat info na bytecode
    if "prefix" in info and info["prefix"] is not None:
        output.append(info["prefix"])

    output.append(info["opcode"])

    if "modrm" in info:
        output.append(info["modrm"])

    output.extend(info["data"])

    return output

def calculate_value(arg: str, labels: dict[str, int]) -> int:
    parts = re.split(r"(?=[+-])", arg) # Splits by + and -, but keeps it in
    runnung_sum = 0

    for part in parts:
        if part == "":
            continue
        
        sign = "-" if part[0] == "-" else "+"
        part = part.replace(sign, "")
        part = part.strip()

        part_val = 0

        if part[0].isdigit():
            part_val = parse_number(part)
        else:
            assert part in labels, f"Label \"{part}\" is not defined"
            part_val = labels[part]

        runnung_sum += part_val if sign == "+" else -part_val

    return runnung_sum

def int_to_bytes(val: int, size: int) -> list[int]:
    output = []

    for _ in range(size // 8):
        output.append(val % 2**8)
        val //= 2**8

    return output

if __name__ == "__main__":
    # print(calculate_value("42", {}))
    # print(calculate_value("42+42", {}))
    # print(calculate_value("42-42", {}))
    # print(calculate_value("42+42-42", {}))
    # print(calculate_value("lbl", {"lbl": 42}))
    # print(calculate_value("lbl+42", {"lbl": 42}))
    # print(calculate_value("lbl-42", {"lbl": 42}))
    # print(calculate_value("lbl- 42 + NoTomeUndefined", {"lbl": 42}))
    print(matches_args(["3"], ["3"]))
    code = """
segment code
label   MOV AX, 7
        MOV BX, 42
        ADD AX, BX
        INC AX
        HLT
    """

    code2 = """
segment code
label   DEC byte [BX]
"""


    # program = assemble("segment code \nllaabel ADD AX, BX")
    program = assemble(code2)
    print(program)

    # assemble("segment code \nllaabel JMP lbl_02")


    
    ...


