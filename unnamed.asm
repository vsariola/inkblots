
org 100h

main:    
    mov     di, 512
.loop:
    lodsb
    aam     16    
    stosb
    xchg    al, ah
    stosb
    loop    .loop


    mov al, 13h
    int 10h
