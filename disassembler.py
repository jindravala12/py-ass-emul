

def parse_next_instruction(program, IP):
    """Just in time dissasembler"""
    instruction = Instruction()
    span = 0

    def load_next():
        nonlocal span
        byte = program[IP + span]
        span += 1
        instruction.bytes.append(byte)
        return byte

    byte = load_next()
    operation, properties = OPCODES[byte]

    if "prefix" in properties:
        instruction.prefix = operation

        byte = load_next()
        operation, properties = OPCODES[byte]

    instruction.operation = operation

    # Handle GRP instructions
    if instruction.operation in GRPs:
        instruction.modrm = ModRM(load_next(), properties[1] == "b", load_next)
        instruction.operation, sp_properties = GRPs[instruction.operation][instruction.modrm.reg_val]

        if sp_properties != "":
            properties = sp_properties

    for arg in properties.split():
        # Codes that don't need ModRM byte:
        # (Do not wory, it would read ModR/M. Codes are structured, so that this wouldn't happen)
        if arg in REGISTERS:
            instruction.arguments.append(Register(arg))
            continue

        if "1" in arg:
            instruction.arguments.append(Immutable(1))
        if "3" in arg:
            instruction.arguments.append(Immutable(3))

        if arg[0] == "O":
            byte = load_next() + load_next() * 2**8
            instruction.arguments.append(byte)
            continue

        if arg[0] == "I":
            byte = load_next()
            if arg[1] != "b":
                byte = byte + load_next() * 2**8

            instruction.arguments.append(Immutable(byte))
            continue

        if arg[0] == "A":
            raise NotImplementedError("TODO: dodělat")
            continue

        # From here, all instructions do need ModR/M
        if instruction.modrm is None:
            instruction.modrm = ModRM(load_next(), arg[1] == "b", load_next)

        match arg[0]:
            case "G":
                instruction.arguments.append(instruction.modrm.reg)
            case "E":
                instruction.arguments.append(instruction.modrm.rm)
            case "S":
                instruction.arguments.append(
                    Register(SEG_REGS[instruction.modrm.reg_val])
                )
            case "M":
                raise NotImplementedError(
                    "Not relevant for KSI emulator.")  # TODO: better hláška
            case _:
                raise Exception("Unrecognised instruction property")

    return instruction


def parse_number(s: str) -> int:
    if s[-1] == "h":
        return int(s[:-1], 16)
    if s[-1] == "b":
        return int(s[:-1], 2)
    return int(s)


RM_8_REGS = ["AL", "CL", "DL", "BL", "AH", "CH", "DH", "BH"]
RM_16_REGS = ["AX", "CX", "DX", "BX", "SP", "BP", "SI", "DI"]

SEG_REGS = ["ES", "CS", "SS", "DS", "FS", "GS"]

# !! If mod=00, Místo BP je pouze displacement16!!
MOD_00_RM = ["BX+SI", "BX+DI", "BP+SI", "BP+DI", "SI", "DI", "BP", "BX"]

REGISTERS = set(RM_8_REGS + RM_16_REGS + SEG_REGS)


OPCODES = [
    # Parsed from http://www.mlsite.net/8086/#tbl_map1
    # 0x0_
    ('ADD', 'Eb Gb'), ('ADD', 'Ev Gv'), ('ADD', 'Gb Eb'), ('ADD',
                                                           'Gv Ev'), ('ADD', 'AL Ib'), ('ADD', 'AX Iv'), ('PUSH', 'ES'), ('POP', 'ES'),
    ('OR', 'Eb Gb'), ('OR', 'Ev Gv'), ('OR', 'Gb Eb'), ('OR',
                                                        'Gv Ev'), ('OR', 'AL Ib'), ('OR', 'AX Iv'), ('PUSH', 'CS'), ('', ''),

    # 0x1_
    ('ADC', 'Eb Gb'), ('ADC', 'Ev Gv'), ('ADC', 'Gb Eb'), ('ADC',
                                                           'Gv Ev'), ('ADC', 'AL Ib'), ('ADC', 'AX Iv'), ('PUSH', 'SS'), ('POP', 'SS'),
    ('SBB', 'Eb Gb'), ('SBB', 'Ev Gv'), ('SBB', 'Gb Eb'), ('SBB',
                                                           'Gv Ev'), ('SBB', 'AL Ib'), ('SBB', 'AX Iv'), ('PUSH', 'DS'), ('POP', 'DS'),

    # 0x2_
    ('AND', 'Eb Gb'), ('AND', 'Ev Gv'), ('AND', 'Gb Eb'), ('AND',
                                                           'Gv Ev'), ('AND', 'AL Ib'), ('AND', 'AX Iv'), ('ES:', 'prefix'), ('DAA', ''),
    ('SUB', 'Eb Gb'), ('SUB', 'Ev Gv'), ('SUB', 'Gb Eb'), ('SUB',
                                                           'Gv Ev'), ('SUB', 'AL Ib'), ('SUB', 'AX Iv'), ('CS:', 'prefix'), ('DAS', ''),

    # 0x3_
    ('XOR', 'Eb Gb'), ('XOR', 'Ev Gv'), ('XOR', 'Gb Eb'), ('XOR',
                                                           'Gv Ev'), ('XOR', 'AL Ib'), ('XOR', 'AX Iv'), ('SS:', 'prefix'), ('AAA', ''),
    ('CMP', 'Eb Gb'), ('CMP', 'Ev Gv'), ('CMP', 'Gb Eb'), ('CMP',
                                                           'Gv Ev'), ('CMP', 'AL Ib'), ('CMP', 'AX Iv'), ('DS:', 'prefix'), ('AAS', ''),

    # 0x4_
    ('INC', 'AX'), ('INC', 'CX'), ('INC', 'DX'), ('INC',
                                                  'BX'), ('INC', 'SP'), ('INC', 'BP'), ('INC', 'SI'), ('INC', 'DI'),
    ('DEC', 'AX'), ('DEC', 'CX'), ('DEC', 'DX'), ('DEC',
                                                  'BX'), ('DEC', 'SP'), ('DEC', 'BP'), ('DEC', 'SI'), ('DEC', 'DI'),

    # 0x5_
    ('PUSH', 'AX'), ('PUSH', 'CX'), ('PUSH', 'DX'), ('PUSH',
                                                     'BX'), ('PUSH', 'SP'), ('PUSH', 'BP'), ('PUSH', 'SI'), ('PUSH', 'DI'),
    ('POP', 'AX'), ('POP', 'CX'), ('POP', 'DX'), ('POP',
                                                  'BX'), ('POP', 'SP'), ('POP', 'BP'), ('POP', 'SI'), ('POP', 'DI'),

    # 0x6_  Not relevant for KSI emulator
    ('--', ''), ('--', ''), ('--', ''), ('--',
                                         ''), ('--', ''), ('--', ''), ('--', ''), ('--', ''),
    ('--', ''), ('--', ''), ('--', ''), ('--',
                                         ''), ('--', ''), ('--', ''), ('--', ''), ('--', ''),

    # 0x7_
    ('JO', 'Jb'), ('JNO', 'Jb'), ('JB', 'Jb'), ('JNB', 'Jb'), ('JZ',
                                                               'Jb'), ('JNZ', 'Jb'), ('JBE', 'Jb'), ('JA', 'Jb'),
    ('JS', 'Jb'), ('JNS', 'Jb'), ('JPE', 'Jb'), ('JPO',
                                                 'Jb'), ('JL', 'Jb'), ('JGE', 'Jb'), ('JLE', 'Jb'), ('JG', 'Jb'),

    # 0x8_
    ('GRP1', 'Eb Ib'), ('GRP1', 'Ev Iv'), ('GRP1', 'Eb Ib'), ('GRP1', 'Ev Ib'), ('TEST',
                                                                                 'Gb Eb'), ('TEST', 'Gv Ev'), ('XCHG', 'Gb Eb'), ('XCHG', 'Gv Ev'),
    ('MOV', 'Eb Gb'), ('MOV', 'Ev Gv'), ('MOV', 'Gb Eb'), ('MOV',
                                                           'Gv Ev'), ('MOV', 'Ew Sw'), ('LEA', 'Gv M'), ('MOV', 'Sw Ew'), ('POP', 'Ev'),

    # 0x9_
    ('NOP', ''), ('XCHG', 'CX AX'), ('XCHG', 'DX AX'), ('XCHG', 'BX AX'), ('XCHG',
                                                                           'SP AX'), ('XCHG', 'BP AX'), ('XCHG', 'SI AX'), ('XCHG', 'DI AX'),
    ('CBW', ''), ('CWD', ''), ('CALL', 'Ap'), ('WAIT',
                                               ''), ('PUSHF', ''), ('POPF', ''), ('SAHF', ''), ('LAHF', ''),

    # 0xA_
    ('MOV', 'AL Ob'), ('MOV', 'AX Ov'), ('MOV', 'Ob AL'), ('MOV',
                                                           'Ov AX'), ('MOVSB', ''), ('MOVSW', ''), ('CMPSB', ''), ('CMPSW', ''),
    ('TEST', 'AL Ib'), ('TEST', 'AX Iv'), ('STOSB', ''), ('STOSW',
                                                          ''), ('LODSB', ''), ('LODSW', ''), ('SCASB', ''), ('SCASW', ''),

    # 0xB_
    ('MOV', 'AL Ib'), ('MOV', 'CL Ib'), ('MOV', 'DL Ib'), ('MOV', 'BL Ib'), ('MOV',
                                                                             'AH Ib'), ('MOV', 'CH Ib'), ('MOV', 'DH Ib'), ('MOV', 'BH Ib'),
    ('MOV', 'AX Iv'), ('MOV', 'CX Iv'), ('MOV', 'DX Iv'), ('MOV', 'BX Iv'), ('MOV',
                                                                             'SP Iv'), ('MOV', 'BP Iv'), ('MOV', 'SI Iv'), ('MOV', 'DI Iv'),

    # 0xC_
    ('', ''), ('', ''), ('RET', 'Iw'), ('RET', ''), ('LES',
                                                     'Gv Mp'), ('LDS', 'Gv Mp'), ('MOV', 'Eb Ib'), ('MOV', 'Ev Iv'),
    ('', ''), ('', ''), ('RETF', 'Iw'), ('RETF', ''), ('INT',
                                                       '3'), ('INT', 'Ib'), ('INTO', ''), ('IRET', ''),

    # 0xD_
    ('GRP2', 'Eb 1'), ('GRP2', 'Ev 1'), ('GRP2', 'Eb CL'), ('GRP2',
                                                            'Ev CL'), ('AAM', 'I0'), ('AAD', 'I0'), ('', ''), ('XLAT', ''),
    ('CO-PROCESSOR INSTRUCTIONS', ''), ('--', ''), ('--',
                                                    ''), ('--', ''), ('--', ''), ('--', ''), ('--', ''), ('--', ''),

    # 0xE_
    ('LOOPNZ', 'Jb'), ('LOOPZ', 'Jb'), ('LOOP', 'Jb'), ('JCXZ', 'Jb'), ('IN',
                                                                        'AL Ib'), ('IN', 'AX Ib'), ('OUT', 'Ib AL'), ('OUT', 'Ib AX'),
    ('CALL', 'Jv'), ('JMP', 'Jv'), ('JMP', 'Ap'), ('JMP', 'Jb'), ('IN',
                                                                  'AL DX'), ('IN', 'AX DX'), ('OUT', 'DX AL'), ('OUT', 'DX AX'),

    # 0xF_
    ('LOCK', ''), ('', ''), ('REPNZ', ''), ('REPZ', ''), ('HLT',
                                                          ''), ('CMC', ''), ('GRP3a', 'Eb'), ('GRP3b', 'Ev'),
    ('CLC', ''), ('STC', ''), ('CLI', ''), ('STI', ''), ('CLD',
                                                         ''), ('STD', ''), ('GRP4', 'Eb'), ('GRP5', 'Ev'),
]

GRPs = {
    "GRP1": [('ADD', ''), ('OR', ''), ('ADC', ''), ('SBB', ''), ('AND', ''), ('SUB', ''), ('XOR', ''), ('CMP', '')],
    "GRP2": [('ROL', ''), ('ROR', ''), ('RCL', ''), ('RCR', ''), ('SHL', ''), ('SHR', ''), ('--', ''), ('SAR', '')],
    "GRP3a": [('TEST', 'Eb Ib'), ('--', ''), ('NOT', ''), ('NEG', ''), ('MUL', ''), ('IMUL', ''), ('DIV', ''), ('IDIV', '')],
    "GRP3b": [('TEST', 'Ev Iv'), ('--', ''), ('NOT', ''), ('NEG', ''), ('MUL', ''), ('IMUL', ''), ('DIV', ''), ('IDIV', '')],
    "GRP4": [('INC', ''), ('DEC', ''), ('--', ''), ('--', ''), ('--', ''), ('--', ''), ('--', ''), ('--', '')],
    "GRP5": [('INC', ''), ('DEC', ''), ('CALL', ''), ('CALL', 'Mp'), ('JMP', ''), ('JMP', 'Mp'), ('PUSH', ''), ('--', '')]
}


class Instruction:
    def __init__(self):
        self.operation: str = None
        self.prefix: None | str = None  # None | "DS" | "CS" | ...
        self.arguments: list[Parameter] = []

        self.size = 0   # 0 for RET; 1 for MOV AL, AH; 2 for MOV AX, BX

        self.bytes = []  # Aspoň aby tu něco bylo
        self.modrm: ModRM | None = None


class Register:
    def __init__(self, name):
        self.name: str = name
        self.size: int = 8 if name[1] in ['L', 'H'] else 16


class ModRM:
    def __init__(self, byte, is_8b: bool, load_byte):
        self.byte = byte  # Asi k ničemu, ale třeba se to bude hodit TODO: Vymaž before release

        self.mod: int = byte // 64
        self.reg_val: int = (byte // 8) % 8
        self.rm_val: int = byte % 8

        # self.reg: Register
        # so that there couldn't be None - TODO: rewrite
        self.rm: Memmory | Register = Register("Dummy")

        # Reg
        regs = RM_8_REGS if is_8b else RM_16_REGS
        self.reg: Register = Register(regs[self.reg_val])

        # R/M
        if self.mod == 3:
            self.rm = Register(regs[self.rm_val])
        else:
            if self.mod == 0 and self.rm_val == 6:
                displ = load_byte() + load_byte() * 2**8
                self.rm = Memmory(None, displ)
            else:
                displ = 0
                if self.mod >= 1:
                    displ = load_byte()

                if self.mod == 2:
                    displ = displ + load_byte() * 2**8

                self.rm = Memmory(MOD_00_RM[self.rm_val], displ)


class Immutable:
    def __init__(self, value):
        self.value = value


class Pointer:
    def __init__(self, segment: int, offset: int):
        self.segment = segment
        self.offset = offset


class Memmory:
    def __init__(self, source: str | None, displacement: int, segment="DS"):
        self.displacement: int = displacement
        self.segment = segment

        # Is None when mod=00 and rm=110
        self.source: str | None = source


class Label:
    def __init__(self, label: str, displacement: int = 0, include_segment=False):
        self.label = label
        self.displacement: int = displacement
        self.include_segment = include_segment


Parameter = Register | Immutable | Memmory | Pointer
ParameterOrLabel = Parameter | Label


if __name__ == "__main__":
    x = parse_next_instruction([
        0x38,  # CMP BL, DH
        0xF3,
    ], 0)

    x = parse_next_instruction([
        0x80,
        0xFB,
        0x06,
    ], 0)

    x = parse_next_instruction([
        0xFE,
        0xC0,
        0x23,
        0x01,
        0x07,
    ], 0)

    x = parse_next_instruction([
        0xF7,
        0xD8,
    ], 0)

    print(x)

    # p = parse_param("AX")
    # p = parse_param("25")
    # p = parse_param("11b")
    # p = parse_param("[BX+SI+24h]")
    # p = parse_param("[n]")

    # print(p)


"""
Co zbývá:
ASSEMBLER
- Zbýva prakticky vše
Koncipované je to takto:
1) Parsing parametrů
2) Podle instrukce a parametrů vytvořit bytecode
- problémy: assembler by měl zvládat základní matiku - např. MOV [n + 3], 4*5+1   --> MOV [(n+3)], 21


DISASSEMBLER
- Zpracování pointerů


EMULÁTOR
- vymyslet ukládání programu (seznam segmentů / seznam všech bajtů programu)
- udělat vzorové řešení (dopsat předpřipravené funkce)
- otestovat
"""
