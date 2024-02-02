

org 100h

%define STEPS 16
%define ITERS 12
%define STEPSIZEDIV 150000
%define SCALE -0.3
%define MINDIST 0.001
%define CAM_Y -0.28
%define CAM_Z -0.35
%define LEVEL 1.73

main:
    .chordprog:
    db      1,1,0,1                     ; this is the chord progresion data but assembles into harmless instructions
    mov     ax, 351Ch                   ; int 21h: ah = 35h get interrupt handler, al = 1Ch which interrupt
    int     21h                         ; returns the handler in es:bx
    push    es                          ; save the current handler to be able to restore it
    push    bx
    mov     dx, interrupt               ; dx = New handler address
    mov     ax, 0x13                    ; mode 13h
    call    init                        ; into known values (in particular, to have chn 3 initialize as 0).
    push    0xa000 - 10-20*3            ; set es to video segment, shifting 3.5 lines (the top three lines had some visual glitch).
    pop     es
.mainloop:
    sub     dh, 0x68                    ; dh = y, shift it to center the coordinates
    pusha
    mov     bx,-12
    mov     cx, STEPS-1
    fld     dword [c_camz]
    fld     dword [c_camy]
    fild    word [time]
    fidiv   word [c_i1024]
.marchloop:
    fld     st0
    fisub   word [channel_0+100]
    fcos
    fldl2t
    .mut_o  equ $-1
    faddp   st1, st0
    fldpi
    fdivp   st1, st0
    fstp    dword [bx-100]
    fild    word [channel_drums+100]                 ; stack: r px py pz, o is at [bx-100]
    fcos
    fld     st3
    fld     st3
    fld     st3         ; stack: tx ty tz r px py pz, o is at [bx-100]
    mov     dx, ITERS
.maploop:
    fld     st0          ; tx tx
    frndint              ; round(tx) tx
    fsubp   st1, st0     ; tx-round(tx)
    fabs                 ; tx = abs(tx-round(tx))
    fxch    st2, st0
    fxch    st1, st0
    fadd    st0          ; tx*=2
    fld     st0
    fmul    st0          ; tx*tx tx
    faddp   st4, st0     ; r += tx*tx; tx ty ....
    fld     st2
    fmul    dword [bx-100]
    faddp   st1, st0
    fld     st0
    fmul    dword [bx-100]
    fsubp   st3, st0
    dec     dx
    jnz     .maploop
    fstp    st0
    fstp    st0
    fstp    st0
    fsqrt
    fsub    dword [c_level]

    fild    word [bx]
    fmul    st0, st1
    .mut_yglitch equ $-1
    fidiv   dword [c_stepsizediv]
    faddp   st3

    fild    dword [c_zstep]
    fild    word [bx-1]
    fld     st1
    fmul    dword [c_camz]
    fsubp   st1
    fld     st0
    fmul    dword [c_camz]
    faddp   st2

    fxch    st1, st0
    .mut_camdir equ $-1
    fmul    st0, st2
    fidiv   dword [c_stepsizediv]
    faddp   st3

    fmul    st0, st1
    fidiv   dword [c_stepsizediv]
    faddp   st4

    fld     dword [c_mindist]
    fcomp   st1 ; dist<MINDIST
    fnstsw  ax
    test    ah, 0x01
    fstp    st0
    jz      .out
    loop    trampoline
.out:
    fstp    st0
    fstp    st0
    fstp    st0
    mov      [bx+2],cx
    popa
    mov     al, 31
    sub     al, cl
    stosb                               ; di = current pixel, write al to screen
    imul    di, 85                      ; traverse the pixels in slightly random order (tip from HellMood)
    mov     ax, 0xCCCD                  ; Rrrola trick!
    mul     di                          ; dh = y, dl = x
    xchg    bx, ax                      ; HellMood: put the low word of multiplication to bx, so we have more precision
    jc      .mainloop                   ; when loading it in FPU
    xor     ax, ax
    in      al, 0x60                    ; check for ESC key
    dec     ax
    jnz     trampoline2                 ; mutate this when the song ends
    .looptarget equ $-1
    mov     dx, 0x330
    mov     cl, 0xBF
.noteoffloop:                           ; turn off all notes
    mov     al, cl
    out     dx, al
    mov     al, 0x7B
    out     dx, al
    salc
    out     dx, al
    loop    .noteoffloop
    pop     dx
    pop     ds
    mov     al, 3                       ; text mode
init:
    int     10h
    mov     ax, 251Ch
    int     21h
    ret

trampoline:
    jmp     main.marchloop

trampoline2:
    jmp     main.mainloop


interrupt:
    pusha
    mov     bp, word [time]
    mov     bx, main.chordprog
    mov     ax, bp
    shr     al, 6
    xlatb
    mov     [.chord], al
    mov     dx, 0x330
    mov     di, 48
    mov     si, channel_0
.loop:
    test    bp, bp
    jnz     .skipreset
    xor     ax, ax
    mov     [si+100], al
.skipreset
    lodsb
    mov     cx, bp
    shr     cx, 8
    bt      [si], cx
    jnc     .skip
    mov     bx, bp
.increment:
    shr     bx, 1
    jc      .skip
    shr     al, 1
    jnz     .increment
    and     bx, 7
    inc     si ; this is actually a bug. but gives a nice effect so I kept it
    mov     al, [si+bx]
    test    al, al
    jz      .skip
    add     si, 8
    cmp     di, 12
    je      .drums
    add     al, 1
.chord equ $-1
    mov     cl, 12
    mul     cl
    mov     cl, 7
    div     cl
    add     ax, 12*5-48
    add     ax, di
.drums:
    mov     cx, 6
    rep     outsb
    mov     [si-channel_1+channel_0+100], al
    out     dx, al
    mov     al, 127
    out     dx, al
    jmp     .done
.skip:
    add     si, 15
.done:
    sub     di, 12
    jnz     .loop
    inc     bp               ; increment time
    mov     word [time], bp
    test    bp, 0xFF
    jnz     .noadvance
    mov     bh, 0x01
    mov     ax, word [script]
    .scriptpos equ $-2
    mov     bl, ah
    mov     byte [bx], al           ; change part of the code based on demo part
    add     word [.scriptpos],2     ; advance the script position by 2
.noadvance:
    popa
    iret

    db 0 ; padding to make the intro 512b :)

script:
    db 0xE8, main.mut_o
    db 0xC8, main.mut_camdir
    db 0xC9, main.mut_camdir
    db 3,    main.chordprog+1
    db 0xC9, main.mut_camdir
    db 0xC8, main.mut_camdir
    db 0xC1, main.mut_yglitch
    db 0xFD, main.looptarget

time:
    dw      0x0

c_camy:
    dd      CAM_Y

c_camz:
    dd      CAM_Z

c_mindist:
    dd      MINDIST

c_level:
    dd      LEVEL

c_stepsizediv:
    dd      STEPSIZEDIV

c_i1024:
    dw      1024

channel_0:
    db      (1 << 5)-1        ; how quickly the channel plays notes
    db      11110000b         ; when is the channel active
    db      1,0,3,2,1,0,3,4   ; what pattern the channel is playing
    db      0xC8              ; MIDI command: set instrument
    db      89
    db      0xB8              ; MIDI command: release all channel notes
    db      0x7B
    db      0
    db      0x98              ; MIDI command: trigger note (the note and volume come programmatically)

channel_1:
    db      (1 << 3)-1
    db      01111111b
    db      1,0,5,1,0,1,3,2
    db      0xC7
    db      33
    db      0xB7
    db      0x7B
    db      0
    db      0x97

channel_2:
    db      (1 << 6)-1
    db      11111110b
    db      1,3,1,4,1,3,1,1
    db      0xC6
    db      94
    db      0xB6
    db      0x7B
    db      0
    db      0x96

channel_drums:
    db      (1 << 2)-1
    db      01101100b
    db      10+25,0,29+25,2+25,8+25,0,29+25,0
    db      0xC2
c_zstep:
    dd      256*256/2
    db      0x99
