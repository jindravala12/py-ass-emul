
class assembler:

    def __init__(self):
        self.INSTRUCTIONS = {
            'ADD': [('Eb Gb', 0), ('Ev Gv', 1), ('Gb Eb', 2), ('Gv Ev', 3), ('AL Ib', 4), ('AX Iv', 5)],
            'PUSH': [('ES', 6), ('CS', 14), ('SS', 22), ('DS', 30), ('AX', 80), ('CX', 81), ('DX', 82), ('BX', 83), ('SP', 84), ('BP', 85), ('SI', 86), ('DI', 87)],
            'POP': [('ES', 7), ('SS', 23), ('DS', 31), ('AX', 88), ('CX', 89), ('DX', 90), ('BX', 91), ('SP', 92), ('BP', 93), ('SI', 94), ('DI', 95), ('Ev', 143)],
            'OR': [('Eb Gb', 8), ('Ev Gv', 9), ('Gb Eb', 10), ('Gv Ev', 11), ('AL Ib', 12), ('AX Iv', 13)],
            'ADC': [('Eb Gb', 16), ('Ev Gv', 17), ('Gb Eb', 18), ('Gv Ev', 19), ('AL Ib', 20), ('AX Iv', 21)],
            'SBB': [('Eb Gb', 24), ('Ev Gv', 25), ('Gb Eb', 26), ('Gv Ev', 27), ('AL Ib', 28), ('AX Iv', 29)],
            'AND': [('Eb Gb', 32), ('Ev Gv', 33), ('Gb Eb', 34), ('Gv Ev', 35), ('AL Ib', 36), ('AX Iv', 37)],
            'DAA': [('', 39)], 'SUB': [('Eb Gb', 40), ('Ev Gv', 41), ('Gb Eb', 42), ('Gv Ev', 43), ('AL Ib', 44), ('AX Iv', 45)],
            'DAS': [('', 47)], 'XOR': [('Eb Gb', 48), ('Ev Gv', 49), ('Gb Eb', 50), ('Gv Ev', 51), ('AL Ib', 52), ('AX Iv', 53)],
            'SS:': [('prefix', 54)],
            'AAA': [('', 55)],
            'CMP': [('Eb Gb', 56), ('Ev Gv', 57), ('Gb Eb', 58), ('Gv Ev', 59), ('AL Ib', 60), ('AX Iv', 61)],
            'AAS': [('', 63)],
            'INC': [('AX', 64), ('CX', 65), ('DX', 66), ('BX', 67), ('SP', 68), ('BP', 69), ('SI', 70), ('DI', 71)], 'DEC': [('AX', 72), ('CX', 73), ('DX', 74), ('BX', 75), ('SP', 76), ('BP', 77), ('SI', 78), ('DI', 79)],
            'JO': [('Jb', 112)],
            'JNO': [('Jb', 113)],
            'JB': [('Jb', 114)],
            'JNB': [('Jb', 115)],
            'JZ': [('Jb', 116)],
            'JNZ': [('Jb', 117)],
            'JBE': [('Jb', 118)],
            'JA': [('Jb', 119)],
            'JS': [('Jb', 120)],
            'JNS': [('Jb', 121)],
            'JPE': [('Jb', 122)],
            'JPO': [('Jb', 123)],
            'JL': [('Jb', 124)],
            'JGE': [('Jb', 125)],
            'JLE': [('Jb', 126)],
            'JG': [('Jb', 127)],
            'GRP1': [('Eb Ib', 128), ('Ev Iv', 129), ('Eb Ib', 130), ('Ev Ib', 131)],
            'TEST': [('Gb Eb', 132), ('Gv Ev', 133), ('AL Ib', 168), ('AX Iv', 169)],
            'XCHG': [('Gb Eb', 134), ('Gv Ev', 135), ('CX AX', 145), ('DX AX', 146), ('BX AX', 147), ('SP AX', 148), ('BP AX', 149), ('SI AX', 150), ('DI AX', 151)],
            'MOV': [('Eb Gb', 136), ('Ev Gv', 137), ('Gb Eb', 138), ('Gv Ev', 139), ('Ew Sw', 140), ('Sw Ew', 142), ('AL Ob', 160), ('AX Ov', 161), ('Ob AL', 162), ('Ov AX', 163), ('AL Ib', 176), ('CL Ib', 177), ('DL Ib', 178), ('BL Ib', 179), ('AH Ib', 180), ('CH Ib', 181), ('DH Ib', 182), ('BH Ib', 183), ('AX Iv', 184), ('CX Iv', 185), ('DX Iv', 186), ('BX Iv', 187), ('SP Iv', 188), ('BP Iv', 189), ('SI Iv', 190), ('DI Iv', 191), ('Eb Ib', 198), ('Ev Iv', 199)],
            'LEA': [('Gv M', 141)],
            'NOP': [('', 144)],
            'CBW': [('', 152)],
            'CWD': [('', 153)],
            'CALL': [('Ap', 154), ('Jv', 232)],
            'WAIT': [('', 155)], 'PUSHF': [('', 156)], 'POPF': [('', 157)], 'SAHF': [('', 158)], 'LAHF': [('', 159)], 'MOVSB': [('', 164)], 'MOVSW': [('', 165)], 'CMPSB': [('', 166)], 'CMPSW': [('', 167)], 'STOSB': [('', 170)], 'STOSW': [('', 171)], 'LODSB': [('', 172)], 'LODSW': [('', 173)], 'SCASB': [('', 174)],
            'SCASW': [('', 175)],
            'RET': [('Iw', 194), ('', 195)],
            'LES': [('Gv Mp', 196)],
            'LDS': [('Gv Mp', 197)],
            'RETF': [('Iw', 202), ('', 203)],
            'INT': [('3', 204), ('Ib', 205)],
            'INTO': [('', 206)],
            'IRET': [('', 207)],
            'GRP2': [('Eb 1', 208), ('Ev 1', 209), ('Eb CL', 210), ('Ev CL', 211)],
            'AAM': [('I0', 212)],
            'AAD': [('I0', 213)],
            'XLAT': [('', 215)],
            'LOOPNZ': [('Jb', 224)],
            'LOOPZ': [('Jb', 225)],
            'LOOP': [('Jb', 226)],
            'JCXZ': [('Jb', 227)],
            'IN': [('AL Ib', 228), ('AX Ib', 229), ('AL DX', 236), ('AX DX', 237)],
            'OUT': [('Ib AL', 230), ('Ib AX', 231), ('DX AL', 238), ('DX AX', 239)],
            'JMP': [('Jv', 233), ('Ap', 234), ('Jb', 235)],
            'LOCK': [('', 240)],
            'REPNZ': [('', 242)],
            'REPZ': [('', 243)],
            'HLT': [('', 244)],
            'CMC': [('', 245)],
            'GRP3a': [('Eb', 246)],
            'GRP3b': [('Ev', 247)],
            'CLC': [('', 248)],
            'STC': [('', 249)],
            'CLI': [('', 250)],
            'STI': [('', 251)],
            'CLD': [('', 252)],
            'STD': [('', 253)],
            'GRP4': [('Eb', 254)],
            'GRP5': [('Ev', 255)]}

    def assemble(self, program: str) -> list[int]:
        byte_num = 0
        assembled: list[int | str] = []
        variables: dict[str, int | None] = {}
        lines = program.split("\n")

        for i in range(len(lines)):
            byte_num += self.process_line(lines[i],
                                          assembled, variables, byte_num, i)

        for variable, val in variables.items():
            if val is None:
                raise Exception(f"{variable} is undefined")

        for i in range(len(assembled)):
            fuck_mypy = assembled[i]
            if isinstance(fuck_mypy, str):
                byte_val = variables[fuck_mypy]
                assert byte_val is not None
                assembled[i] = byte_val

        # it is what it is mypy
        return assembled

    def process_line(self, line, assembled, vars, byte_num, line_num):
        valid_tokens = 0
        var_in_line = False
        line = line.split(" ")

        for token in line:
            if token != "" or token != " ":
                if token[-1] == ",":
                    token = token[:-1]

                if token in self.INSTRUCTIONS:
                    pass
                elif not var_in_line:
                    pass
                else:
                    raise Exception(
                        "invalid combination of op_codes and operands")

        return valid_tokens
