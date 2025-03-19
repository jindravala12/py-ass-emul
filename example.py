from assembler import assemble
from emulator import Emulator

# Dá se i načíst ze souboru (.asm)
code = """
segment	code
..start mov ax, 1
		hlt



		mov bx,data
		mov ds,bx
		mov bx,stack
		mov ss,bx
		mov sp,dno
		
loop_s	mov AH, 0Ah	; Přečíst řádek
		mov DX,nacteno
		int 21h	
		
		JNZ cont
		JMP FAR konec
        
cont 	MOV BX, [nacteno+1]	; delka
	 	MOV byte [BX+2],  0
	 
		mov AH,9	; Vypsat řetězec bajtů na terminál
		mov DX,radek
		int 21h	

        JMP FAR loop_s
	
konec 	HLT
    
segment	data
nacteno	db 80, ?
radek	resb 80


segment	stack
		resb 256
dno		db 0
        
"""


# Převést na bajtkód
program, start, lines_info = assemble(code)

# Inicializovat tím emulátor
e = Emulator(program, start, lines_info)

# [volitelné] Nastavit vstup konzole, upravit maximální počet instrukcí, vypnutí debug módu (vypisování jednotlivých kroků)
e.console_input = "Hello\nWorld\n"
e.max_instructions = 100_000
# e.debugging_mode = False

# Supstit
e.run()

# Výsledek můžete pozorovat např. na registrech, výstupu konzole nebo na statistikách instrukcí
print(e.registers)
print("Console output:", e.console_output.replace("\n", "\\n"))
print(e.statistics)
