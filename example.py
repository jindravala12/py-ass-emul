from assembler import assemble
from emulator import Emulator

# Dá se i načíst ze souboru (.asm)
# code = """
# segment code
# ..start
# 		mov ah 
#         mov bx, data
#         mov ds, bx         ; Loadx data segment

#         mov bx, stack
#         mov ss, bx         ; Load stack segment
#         mov sp, dno        ; Initialize stack pointer

# loop_s
#         mov AH, 0Ah        ; DOS: Buffered input (reads a line)
#         mov DX, nacteno
#         int 21h            ; Read user input
        
#         mov BX, 0          ; BX will store the final number
#         mov SI, radek+1    ; SI points to input buffer (skip first byte)
#         mov CX, [nacteno+1]; Length of input

#         cmp CX, 0
#         je loop_s          ; If no input, repeat

# convert
#         mov AL, [SI]       ; Load character from buffer
#         cmp AL, 13         ; Check for Enter (CR)
#         je done_convert

#         mov DX, 0          ; Clear DX
#         mov AH, 0          ; Clear AH

#         ; Convert ASCII to integer using loops (AL - '0')
#         mov DL, '0'        ; ASCII '0'
# convert_digit
#         cmp AL, DL
#         je digit_found
#         inc DL             ; DL += 1
#         jmp convert_digit

# digit_found
#         mov AL, DL         ; Store the converted digit in AL

#         ; Multiply BX by 10 using loops (since we can't use ADD/SUB)
#         mov DX, BX         ; Save BX to DX
#         shl BX, 1          ; BX * 2
#         mov CX, 4          ; We need BX * 10 = (BX * 2) + (BX * 8)
# multiply_loop
#         shl DX, 1          ; DX * 2
#         loop multiply_loop
#         inc BX             ; BX += 1 (instead of ADD BX, DX)
# multiply_add
#         cmp DX, 0
#         je multiply_done
#         dec DX
#         inc BX
#         jmp multiply_add
# multiply_done

#         ; Add digit to BX using loops
# add_digit
#         cmp AL, 0
#         je digit_added
#         inc BX
#         dec AL
#         jmp add_digit

# digit_added
#         inc SI             ; Move to next character
#         loop convert       ; Process next character

# done_convert
#         mov AX, BX         ; Store result in AX

#         ; Display the number (optional)
#         call print_number

#         JMP loop_s         ; Repeat

# konec
#         HLT                ; Halt the program

# ; ----------------------------------------
# ; Subroutine to print AX as decimal number
# ; ----------------------------------------
# print_number
#         push ax
#         push dx
#         push bx
#         push cx

#         mov CX, 0          ; Digit count
#         mov BX, 10         ; Divisor

# convert_loop
#         mov DX, 0          ; Clear DX
#         mov SI, AX         ; Copy AX
# divide_loop
#         cmp SI, BX
#         jl store_remainder
#         inc DX
#         sub SI, BX
#         jmp divide_loop
# store_remainder
#         push DX            ; Store remainder
#         inc CX             ; Count digits
#         mov AX, SI         ; Store quotient
#         test AX, AX        ; Check if AX == 0
#         jnz convert_loop

# print_loop
#         pop DX             ; Get digit
#         add DL, '0'        ; Convert to ASCII
#         mov AH, 02h        ; DOS: Print character
#         int 21h            ; Print
#         loop print_loop

#         pop cx
#         pop bx
#         pop dx
#         pop ax
#         ret

# segment data
# nacteno    db 80, ?        ; Buffer size (80), actual length stored here
# radek      db 80 dup(?)    ; Buffer for input string

# segment stack
#         resb 256
# dno     db 0

        
# """
code = open("program.asm").read()


# Převést na bajtkód
program, start, lines_info = assemble(code)

# Inicializovat tím emulátor
e = Emulator(program, start, lines_info)

# [volitelné] Nastavit vstup konzole, upravit maximální počet instrukcí, vypnutí debug módu (vypisování jednotlivých kroků)
e.console_input = "40\n"
e.max_instructions = 100_000
#e.debugging_mode = False

# Supstit
e.run()

# Výsledek můžete pozorovat např. na registrech, výstupu konzole nebo na statistikách instrukcí
print(e.registers)
print(e.program)
print("Console output:", e.console_output.replace("\n", "\\n"))
print(e.statistics)
