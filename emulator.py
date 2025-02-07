from disassembler import *
from assembler import assemble
from converting_functions import *


class Emulator:

    def __init__(self, program, start: tuple[int, int] = (0, 0), lines_info: list[tuple[int, str]] = []):
        self.instructions_counter = 0
        self.max_instructions = 10_000

        self.debugging_mode: bool = True

        self.registers = {
            # 16-bitový registr AX je složen ze dvou 8-botivých registrů AH,AL
            "AL": None,
            "AH": None,

            # Platí i pro registry BX, CX, DX
            "BL": None,
            "BH": None,
            "CL": None,
            "CH": None,
            "DL": None,
            "DH": None,

            "SP": None,  # Stack pointer

            "CS": start[0],  # Code segment
            "DS": None,  # Data segment
            "SS": None,  # Stack segment
            "ES": None,  # Extra segment

            "IP": start[1],  # Instruction pointer

            "FL": 0  # Flags register
        }

        self.program = program  # Seznam bajtů
        self.running = True  # Může být uspáno pomocí instrukce HLT

        self.instr_methods = {
            "MOV": self.MOV, "ADD": self.ADD, "ADC": self.ADC,
            "SUB": self.SUB, "SBB": self.SBB, "AND": self.AND,
            "OR": self.OR,   "XOR": self.XOR, "NEG": self.NEG,
            "NOP": self.NOP, "INC": self.INC, "DEC": self.DEC,
            "HLT": self.HLT, "CMP": self.CMP, "TEST": self.TEST,
            "JMP": self.JMP, "CALL": self.CALL, "PUSH": self.PUSH,
            "POP": self.POP, "RET": self.RET, "RETF": self.RETF,
            "INT": self.INT, "TST": self.TEST, "DIV": self.DIV,
            "IDIV": self.IDIV, "IRET": self.IRET, "CBW": self.CBW,
            "RET": self.RET, "RETF": self.RETF, "INT": self.INT,
            "IRET": self.IRET, "CBW": self.CBW
            # Conditional jumps are added later in the code from a dictionary
        }

        self.console_input: str = "Hello\nworld\n"
        self.console_output: str = ""

        self.statistics = {}

        self._complete_instruction_dictionary()

        self.lines_info = lines_info

    def run(self):
        while self.running:
            if self.instructions_counter > self.max_instructions:
                raise Exception(
                    f"Your program executed more than {self.instructions_counter - 1} instructions. There may be an infinite loop.")
            self.instructions_counter += 1

            address = self.get_address("CS", self.get_register("IP"))

            try:
                instr, span = parse_next_instruction(self.program, address)
            except Exception as e:
                raise Exception(f"Error while parsing instruction at address: {address}. Perhaps you've forgotten HLT or you're jumping to wrong address.")

            self.statistics[instr.operation] = self.statistics.get(instr.operation, 0) + 1


            if self.debugging_mode:
                self.debug_print_line(address, instr)

            if instr.operation not in self.instr_methods:
                raise Exception(f"This emulator doesn't support this operation: {instr.operation}")
            
            self.set_register("IP", self.get_register("IP") + span)

            try:
                corresponding_method = self.instr_methods[instr.operation]
                corresponding_method(instr)
            except Exception as e:

                line = self.lines_info.get(address)
                if line is not None:
                    print(f"Error may be related to line {line[0]}:{line[1]}")
                else:
                    print("This error didn't happen handling any of your lines.")

                raise Exception(f"There was an error while handling instruction {instr.operation}:", e)
            

    def _complete_instruction_dictionary(self):
        for instr in SIMPLE_CONDITION_JMPS.keys():
            self.instr_methods[instr] = self.conditional_jump

        for instr in MISSING_CONDITION_JMPS:
            self.instr_methods[instr] = self.conditional_jump

    def get_address(self, segment, offset):
        address = 0

        if isinstance(segment, int):
            address = segment
        elif isinstance(segment, str):
            address = self.get_register(segment)
        else:
            address = self.get_value(segment)
        
        return address * 16 + offset

    def get_memmory(self, arg: Memmory):
        segment = self.get_register(arg.segment)
        offset += arg.displacement

        for reg in arg.source.split("+"):
            offset += self.get_register(reg)

        return segment * 16 + offset

    def get_register(self, reg: str):
        reg = reg.upper()

        if reg[1] == "X":
            output = self.get_register(reg[0]+"H") * 2**8
            output += self.get_register(reg[0]+"L")
            return output

        assert reg in self.registers, f"There is no \"{reg}\" register in this emulator."

        output = self.registers[reg]

        if reg == "DS" and output is None:
            raise Exception("Nemáte nastavený registr pro datový segment.")

        assert output is not None, f"Trying to get value of register {reg} with undefined value."
        return output

    def set_register(self, reg: str, val: int):
        assert val >= 0, f"Do funkce set_register vkládejte hodnotu v přímém kódu, jako nezáporné číslo."

        if reg[1] == "X":
            assert 0 <= val <= 2**16, \
                f"Snažíte se do registru {reg} vložit hodnotu {val}, která je mimo rozsah."
            self.registers[reg[0]+'L'] = val % 2**8
            self.registers[reg[0]+'H'] = val // 2**8
            return

        if reg[1] in ["L", "H"]:
            assert 0 <= val < 2**8
        else:
            assert 0 <= val < 2**16

        self.registers[reg] = val

    def get_byte(self, segment, offset):
        if segment == "ABS":
            seg_val = 0
        else:
            seg_val = self.get_register(segment)
        
        idx = self.get_address(seg_val, offset)
        if idx >= len(self.program):
            raise Exception(f"Trying to get value of undefined byte at {idx}.")

        val = self.program[idx]

        assert val is not None, f"Trying to get value of undefined byte at {idx}."
        return val

    def set_byte(self, segment, offset, value):
        assert 0 <= value <= 2**8
        seg = self.get_register(segment)
        idx = self.get_address(seg, offset)
        
        if idx >= len(self.program):
            raise Exception(f"Trying to set value data out of program memmory.")
        
        self.program[idx] = value

    def get_value(self, arg: Parameter):
        output = None

        match arg:
            case Immutable():
                output = arg.value
            case Memmory():
                offset = arg.displacement
                for reg in arg.source.split("+"):
                    if reg != "":
                        offset += self.get_register(reg)
                output = self.get_byte(arg.segment, offset)
            case Register():
                output = self.get_register(arg.name)

        return output

    def set_value(self, arg, val, size):
        match arg:
            case Register():
                self.set_register(arg.name, val)
            case Memmory():
                offset = arg.displacement

                if arg.source not in ["", None]:
                    for reg in arg.source.split("+"):
                        offset += self.get_register(reg)

                for i in range(size // 8):
                    self.set_byte(arg.segment, offset + i, val % 2**8)
                    val //= 2**8

    # ------- FLAGS: --------
    def set_flag(self, flag: Flag, val: bool):
        f_reg = self.registers["FL"]
        f_reg = f_reg & ~(1 << flag)  # Make the flag 0

        if val:
            f_reg = f_reg | (1 << flag)

        self.registers["FL"] = f_reg

    def get_flag(self, flag: Flag) -> int:
        return (self.registers["FL"] // (2**flag)) % 2

    def update_pf(self, result):
        counter = 0
        for _ in range(8):  # Kontroluje se dolní osmice
            counter += result % 2
            result //= 2

        self.set_flag(PF, counter % 2 == 0)

    def update_zf(self, result):
        self.set_flag(ZF, result == 0)

    def update_sf(self, result, opsize):
        """Sets the sign flag."""
        sign = result // 2**(8*opsize - 1)
        self.set_flag(SF, sign == 1)

    def update_cf(self, result, opsize):
        self.set_flag(CF, result >= 2**opsize)

    def update_of(self, result, opsize):
        """TAKES AS ARGUMENT SIGNED RESULT"""
        is_overflow = 2**(opsize - 1) <= result < 2**(opsize - 1)
        self.set_flag(OF, is_overflow)

    def update_flags(self, result: int, opsize: int, flags: list[int],
                     previous_numbers: list[int] = []  # TODO: Lepší jméno
                     ):
        """Nastaví požadované příznaky. Výsledek vkládejte v přímém kódu s případným přetečením."""
        cropped_result = result % 2**opsize

        if CF in flags:
            self.update_cf(result, opsize)

        if OF in flags:
            raise Exception("Err code: 875. Prosím napiš na diskustní fórum.")
            self.update_of(result, opsize, previous_numbers)

        if SF in flags:
            self.update_sf(cropped_result, opsize)

        if ZF in flags:
            self.update_zf(cropped_result)

        if PF in flags:
            self.update_pf(cropped_result)

    # ======== INSTRUCTIONS: ==========
    # ------- MOVE INSTRUCTIONS: --------

    def MOV(self, instruction: Instruction):
        to_insert = self.get_value(instruction.arguments[1])
        self.set_value(instruction.arguments[0], to_insert, instruction.size)
        # MOV Nenastavouje příznaky

    # ------- ARITMETIC INSTRUCTIONS: --------
    def ADD(self, instruction: Instruction):
        val1 = self.get_value(instruction.arguments[0])
        val2 = self.get_value(instruction.arguments[1])

        result = val1 + val2
        signed_result = from_twos_complement(val1, instruction.size) + \
            from_twos_complement(val2, instruction.size)

        if result > 2**instruction.size:
            self.set_flag(CF, 1)
            result = result % 2**instruction.size

        if 2**(instruction.size - 1) <= signed_result < 2**instruction.size:
            self.set_flag(OF, 1)

        self.set_value(instruction.arguments[0], result % (
            2**instruction.size), instruction.size)
        self.update_flags(result, instruction.size, [ZF, PF, SF])

    def ADC(self, instruction):
        val1 = self.get_value(instruction.arguments[0])
        val2 = self.get_value(instruction.arguments[1])
        cf = 1 if self.get_flag(CF) else 0

        result = val1 + val2 + cf
        signed_result = from_twos_complement(val1, instruction.size) + \
            from_twos_complement(val2, instruction.size) + cf

        self.set_value(instruction.arguments[0], result % (
            2**instruction.size), instruction.size)

        self.update_of(signed_result, instruction.size)
        self.update_cf(result, instruction.size)
        self.update_flags(result, instruction.size, [ZF, PF, SF])

    def SUB(self, instruction):
        val1 = self.get_value(instruction.arguments[0])
        val2 = self.get_value(instruction.arguments[1])

        result = val1 - val2
        signed_result = from_twos_complement(val1, instruction.size) - \
            from_twos_complement(val2, instruction.size)

        self.set_value(
            instruction.arguments[0], result % 2**(instruction.size), instruction.size)
        self.update_of(signed_result, instruction.size)
        self.update_cf(result, instruction.size)
        self.update_flags(result, instruction.size, [ZF, PF, SF])

    def SBB(self, instruction):
        val1 = self.get_value(instruction.arguments[0])
        val2 = self.get_value(instruction.arguments[1])
        cf = 1 if self.get_flag(CF) else 0

        result = val1 - val2 - cf
        signed_result = from_twos_complement(val1, instruction.size) - \
            from_twos_complement(val2, instruction.size) - cf

        self.set_value(
            instruction.arguments[0], result % 2**(instruction.size), instruction.size)
        self.update_of(signed_result, instruction.size)
        self.update_cf(result, instruction.size)
        self.update_flags(result, instruction.size, [ZF, PF, SF])

    def INC(self, instruction):
        val = self.get_value(instruction.arguments[0])
        result = val + 1
        signed_result = from_twos_complement(val, instruction.size) + 1

        self.set_value(instruction.arguments[0], result % (
            2**instruction.size), instruction.size)

        self.update_of(signed_result, instruction.size)
        # CF se nemění
        self.update_flags(val, instruction.size, [ZF, PF, SF])

    def DEC(self, instruction):
        val = self.get_value(instruction.arguments[0])
        result = val - 1
        signed_result = from_twos_complement(val, instruction.size) - 1

        self.set_value(instruction.arguments[0], result % (
            2**instruction.size), instruction.size)

        self.update_of(signed_result, instruction.size)
        # CF se nemění
        self.update_flags(val, instruction.size, [ZF, PF, SF])

    def NEG(self, instruction):
        val = self.get_value(instruction.arguments[0])
        val = ~val + 1
        self.set_value(instruction.arguments[0], val % (
            2**instruction.size), instruction.size)
        self.update_flags(val, instruction.size, [ZF, PF, SF])

    def MUL(self, instruction):
        val = self.get_register("AX" if instruction.size == 16 else "AL")
        val *= self.get_value(instruction.arguments[0])

        self.set_value(Register("AX"), val % 2**16, 16)
        if instruction.size == 16:
            self.set_value(Register("DX"), (val // 2**16) % 2**16, 16)

    def IMUL(self, instruction):
        val = from_twos_complement(self.get_register(
            "AX" if instruction.size == 16 else "AL"), instruction.size)
        val *= from_twos_complement(
            self.get_value(instruction.arguments[0]), instruction.size)

        res = to_twos_complement(val, instruction.size)
        self.set_value(Register("AX"), res % 2**16, 16)
        if instruction.size == 16:
            self.set_value(Register("DX"), (res // 2**16) % 2**16, 16)

    def DIV(self, instruction):
        val = 0
        if instruction.size == 8:
            val = self.get_register("AX")
        else:
            val = self.get_register("DX") * 2**16 + self.get_register("AX")

        divisor = self.get_value(instruction.arguments[0])

        if divisor == 0:
            instr = Instruction()
            instr.operation = "INT"
            instr.arguments = [Immutable(0)]
            self.INT(instr)
            return

        result = val // divisor
        remainder = val % divisor

        if instruction.size == 8:
            self.set_value(Register("AL"), result, 8)
            self.set_value(Register("AH"), remainder, 8)
        else:
            self.set_value(Register("AX"), result, 16)
            self.set_value(Register("DX"), remainder, 16)

    def IDIV(self, instruction):
        val = 0
        if instruction.size == 8:
            val = from_twos_complement(self.get_register("AX"), 16)
        else:
            val = from_twos_complement(self.get_register(
                "DX") * 2**16 + self.get_register("AX"), 16)

        divisor = self.get_value(instruction.arguments[0])

        if divisor == 0:
            instr = Instruction()
            instr.operation = "INT"
            instr.arguments = [Immutable(0)]
            self.INT(instr)
            return

        result = from_twos_complement(val, instruction.size) // \
            from_twos_complement(divisor, instruction.size)
        remainder = from_twos_complement(val, instruction.size) % \
            from_twos_complement(divisor, instruction.size)

        if instruction.size == 8:
            self.set_value(Register("AL"), result, 8)
            self.set_value(Register("AH"), remainder, 8)
        else:
            self.set_value(Register("AX"), result, 16)
            self.set_value(Register("DX"), remainder, 16)

    # ------- LOGIC INSTRUCTIONS: --------

    def AND(self, instruction):
        val1 = self.get_value(instruction.arguments[0])
        val2 = self.get_value(instruction.arguments[1])
        result = val1 & val2

        self.set_value(instruction.arguments[0], result, instruction.size)
        self.update_flags(result, instruction.size, [ZF, PF, SF])

    def OR(self, instruction):
        val1 = self.get_value(instruction.arguments[0])
        val2 = self.get_value(instruction.arguments[1])
        result = val1 | val2

        self.set_value(instruction.arguments[0], result, instruction.size)

        self.update_sf(result, instruction.size)
        self.update_zf(result)
        self.update_pf(result)

    def XOR(self, instruction):
        val1 = self.get_value(instruction.arguments[0])
        val2 = self.get_value(instruction.arguments[1])
        result = val1 ^ val2

        self.set_value(instruction.arguments[0], result, instruction.size)

        self.update_sf(result, instruction.size)
        self.update_zf(result)
        self.update_pf(result)

    def NOT(self, instruction):
        val1 = self.get_value(instruction.arguments[0])
        result = ~val1
        self.set_value(instruction.arguments[0], result, instruction.size)
        # Nemění příznaky

    def CBW(self, instruction):
        val = self.get_register("AL")
        self.set_register("AH", 0 if val < 2**7 else 0xFF)

        # ------- COMPARING INSTRUCTIONS: --------

    def CMP(self, instruction):
        val1 = self.get_value(instruction.arguments[0])
        val2 = self.get_value(instruction.arguments[1])

        result = val1 - val2
        signed_result = from_twos_complement(val1, instruction.size) - \
            from_twos_complement(val2, instruction.size)

        self.update_of(signed_result, instruction.size)
        self.update_flags(result, instruction.size, [CF, ZF, PF, SF])

    def TEST(self, instruction):
        val1 = self.get_value(instruction.arguments[0])
        val2 = self.get_value(instruction.arguments[1])
        result = val1 & val2

        self.update_flags(result, instruction.size, [ZF, PF, SF])
        self.set_flag(CF, 0)
        self.set_flag(OF, 0)

    # ------- PROGRAM BRANCHING INSTRUCTIONS: --------
    def JMP(self, instruction):
        if isinstance(instruction.arguments[0], Pointer):
            # Far jump
            self.set_register("IP", instruction.arguments[0].offset)
            self.set_register("CS", instruction.arguments[0].segment)
        else:
            # Near jump
            assert isinstance(instruction.arguments[0], Immutable)
            where_to = from_twos_complement(
                instruction.arguments[0].value, instruction.size)
            where_to += 1  # TODO: Why +1!?
            where_to += self.get_register("IP")
            where_to %= 2**16

            self.set_register("IP", where_to)

    def CALL(self, instruction: Instruction):
        is_far = isinstance(instruction.arguments[0], Pointer)

        instr = Instruction()
        instr.operation = "PUSH"
        if is_far:
            instr.arguments = [Register("CS")]
            self.PUSH(instr)

        val = self.get_register("IP") + len(instruction.bytes) - 1  # Is safe
        instr.arguments = [Immutable(val)]
        self.PUSH(instr)

        self.JMP(instruction)

    def RET(self, instruction):
        instr = Instruction()
        instr.operation = "POP"
        instr.arguments = [Register("IP")]

        self.POP(instr)

        if instruction.operation == "RETF":
            instr.arguments = [Register("CS")]
            self.POP(instr)

    def RETF(self, instruction):
        self.RET(instruction)

    def relative_jump(self, instruction: Instruction):
        distance = from_twos_complement(
            instruction.arguments[0].value, instruction.size)
        self.set_register("IP", self.get_register("IP") + distance)

    def conditional_jump(self, instruction: Instruction):
        # If is simple condition
        if instruction.operation in SIMPLE_CONDITION_JMPS:
            rules = SIMPLE_CONDITION_JMPS[instruction.operation]

            for flag, expected_value in rules:
                if self.get_flag(flag) != expected_value:
                    return

            self.relative_jump(instruction)
            return

        match instruction.operation:
            case "JL":
                if self.get_flag(SF) != self.get_flag(OF):
                    self.relative_jump(instruction)
            case "JNGE":
                if self.get_flag(SF) != self.get_flag(OF):
                    self.relative_jump(instruction)

            case "JG":
                if self.get_flag(SF) == self.get_flag(OF) and self.get_flag(ZF) == 0:
                    self.relative_jump(instruction)
            case "JNLE":
                if self.get_flag(SF) == self.get_flag(OF) and self.get_flag(ZF) == 0:
                    self.relative_jump(instruction)

            case "JLE":
                if self.get_flag(SF) != self.get_flag(OF) or self.get_flag(ZF) == 1:
                    self.relative_jump(instruction)
            case "JNG":
                if self.get_flag(SF) != self.get_flag(OF) or self.get_flag(ZF) == 1:
                    self.relative_jump(instruction)

            case "JGE":
                if self.get_flag(SF) == self.get_flag(OF):
                    self.relative_jump(instruction)
            case "JNL":
                if self.get_flag(SF) == self.get_flag(OF):
                    self.relative_jump(instruction)
            case _:
                raise Exception(
                    "There was a bug in emulator. Please contact developers. (ErrCode: 435)")

    # ------- STACK INSTRUCTIONS: --------
    def PUSH(self, instruction):
        val = self.get_value(instruction.arguments[0])

        sp = (self.get_register("SP") - 2) % 2**16
        self.set_register("SP", sp)

        self.set_byte('SS', sp, val % 2**8)
        self.set_byte('SS', sp + 1, val // 2**8)

    def POP(self, instruction):
        sp = self.get_register("SP")

        val = self.get_byte('SS', sp)
        val += self.get_byte('SS', sp + 1) * 2**8

        self.set_value(instruction.arguments[0], val, instruction.size)
        self.set_register("SP", (sp + 2) % 2**16)

    # ------- INTERUPT INSTRUCTIONS: --------

    def INT(self, instruction):
        print("Program was interrupted with: INT", instruction.arguments[0].value)

        if instruction.arguments[0].value == 0x21:
            self.INT21h(instruction)
            return
        
        instr = Instruction()
        instr.operation = "PUSH"
        instr.arguments = [Register("FL")]

        self.PUSH(instr)

        self.set_flag(IF, 0)  # Asi uselles v emulátoru, ale tak pro sichr
        self.set_flag(TF, 0)

        instr.arguments = [Register("CS")]
        self.PUSH(instr)
        instr.arguments = [Register("IP")]
        self.PUSH(instr)

        self.set_register("CS", self.get_byte(
            "ABS", instruction.arguments[0].value * 4 + 2))
        self.set_register("IP", self.get_byte(
            "ABS", instruction.arguments[0].value * 4))

    def INT21h(self, instruction):
        """Loads one byte from console."""
        match self.get_register("AH"):
            case 0x01:  # Načíst bajt z konzole
                if self.console_input == "":
                    self.set_register("AL", 0)
                    self.set_flag(ZF, 1)
                else:
                    self.set_register("AL", ord(self.console_input[0]))
                    self.console_input = self.console_input[1:]
                    self.set_flag(ZF, 0)

            case 0x02:  # Vypsat znak
                self.console_output += chr(self.get_register("DL"))

            case 0x09:  # Vypsat řetězec
                offset = self.get_register("DX")
                byte = self.get_byte("DS", offset)
                while byte != 0:
                    self.console_output += chr(byte)
                    offset += 1
                    byte = self.get_byte("DS", offset)

            case 0x0A:  # Načíst řetězec
                offset = self.get_register("DX")
                max_len = self.get_byte("DS", offset)  # Length

                if self.console_input == "":
                    self.set_byte("DS", offset + 1, 0)
                    self.set_byte("DS", offset + 2, 0)
                    self.set_flag(ZF, 1)
                    return

                for i in range(max_len):
                    char = self.console_input[0]
                    self.console_input = self.console_input[1:]

                    if char == "\n":
                        break

                    self.set_byte("DS", offset + i + 2, ord(char))

                self.set_byte("DS", offset + 1, i)

    def IRET(self, instruction):
        instr = Instruction()
        instr.operation = "POP"
        instr.arguments = [Register("IP")]
        self.POP(instr)

        instr.arguments = [Register("CS")]
        self.POP(instr)

        instr.arguments = [Register("FL")]
        self.POP(instr)

        self.set_flag(IF, 1)

    # ------- ANOTHER INSTRUCTIONS: --------

    def NOP(self, instruction):
        pass  # Already implemented ;-)

    def CBW(self, instruction):
        pass

    # ROL, ROR, RCR, RCL - Rotate
    # SAL, SHL, SAR, SHR - Shift

    def HLT(self, instruction):
        # Už jsme ji pro Vás naprogramovali ;-)
        self.running = False
    
    def debug_print_line(self, address: int, instr: Instruction):
        possible_line = self.lines_info.get(address)

        if possible_line is not None:
            print(
                f"Address: {address}, instr: {instr.operation} \tline {possible_line[0]}:{possible_line[1]}")
        elif instr.operation != "NOP":
            print(f"Address: {address}, instr: {instr.operation} \tline (unknown)")


def get_bit(number: int, position: int):
    return (number // 2**position) % 2


if __name__ == "__main__":

    funkcni_cteni_a_psani_na_terminal = """
segment code
        MOV BX, data
        MOV DS, BX

        MOV AL, 9

loop_s  MOV CH, AL
        MOV AH, 1
        INT 21h     ; Load character
        JZ konec
        MOV AH, 2
        MOV DL, AL
        INT 21h     ; Print space
        MOV DL, 32
        INT 21h     ; Print space
        JMP FAR loop_s

konec   HLT


segment data
n       db 97,98,0
"""
    test_code = """
segment code
        MOV BX, data
        MOV DS, BX

        MOV DL, [nums]
        MOV DI, 1
cycle   MOV BL, [nums+DI]
        CMP BL, 0
        JNZ nozero
        JMP end
nozero  CMP BL, DL
        JB bellow
        JMP else
bellow  INC BL
        JMP endif
else    JA above
        JMP endif
above   DEC BL
endif   MOV byte [nums+DI], BL
        ADD DI,1
        JMP cycle
end     HLT

segment data
nums    db 64
        db 66
        db 64
        db 9
        db 0
"""

    code = """
segment vector_preruseni
    db 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
    db 'Hello world'

segment	code
..start	mov bx,data
	mov ds,bx
	mov bx,stack
	mov ss,bx
	mov sp,dno
    MOV BX, muj_stack
    MOV ES, BX

    MOV AX, 7
    MOV ES:[1], AX

	mov dx,mesg
	mov ah,9
	int 21h
	hlt

segment	data
bajt	db 12h
slovo	dw 2356h
mesg	db 'Ahoj','$'

segment	stack
	resb 16
dno:	db ?

segment muj_stack
    db 123
    resb 16

"""

    test3 = """
segment vektor_preruseni
int0    dw hhh
        dw handle0
    
segment code
..start	mov bx,data
        mov ds,bx
        mov bx,stack
        mov ss,bx
        mov sp,dno

        mov AH,2
        mov DL, 'a'
        int 21h
        
        MOV AX, 0
        IDIV AL
        HLT

segment data
        db 0
        resb 16

segment hhh
handle0 mov AH,2
        mov DL, 'x'
        int 21h
        IRET


segment	stack
	resb 16
dno:	db ?

"""

    aaaa = """
segment code
    MOV AX, 0
    MOV BX, 'x'
    HLT
"""

    program, start, lines_info = assemble(test3)

    print(lines_info)

    e = Emulator(program, start, lines_info)
    # e.registers["DS"] = 0  # For debugging purposes
    if not e.run():
        print("Program was stopped because of an error.")
    print(e.registers)
    print(e.program)
    print("Console output:", e.console_output.replace("\n", "\\n"))
