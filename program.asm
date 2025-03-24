
    ; Místo pro načtený řetězec

segment code
..start
    mov BX, data
    mov DS, BX
    jmp nacist
    
    ;mov cl, byte [plus]
    ;HLT              ; Zastavení programu

nacist
    mov AH, 0Ah      ; Nastavení čtení řádku
    mov DX, nacteno  ; Adresa bufferu
    int 21h

    jmp zpracuj

zpracuj
    mov bx, 0
    mov cl, [nacteno+1]
    dec cl
    mov ch, 0
loop_z  
    inc ch
    cmp cl, ch
    dec ch
    mov bl, byte [radek]
    je konec
  
    mov dx, [bx]
    inc ch
    jmp loop_z



konec
    hlt




segment data
plus db 'plus'
minus db 'minus'
krat db 'krat'
nacteno db 80, ?        ; Maximálně 80 znaků, DOS sem zapíše délku
radek   db 80, ?

;mius db 'minus'

