; Hand-reconstructed from REA/Ghidra assembly, not recovered original source.
; Original 2.01 SHA-256: 6401ccfddaf3aa5fe923ddeb5a76423b9216880dff6be2891e38ffcce8716904
; Port roles verified in REA function 0x10366: [8ffe] = UART base + 6 (MSR).
; Each build selects one original function and retains its exact instruction encoding.
BITS 16
CPU 8086

%ifidn ROUTINE, carrier_detect
    ORG 0xaa5c
%elifidn ROUTINE, clear_to_send
    ORG 0xabc1
%else
    %error Select ROUTINE=carrier_detect or ROUTINE=clear_to_send
%endif

    mov dx, [0x8ffe]
    in al, dx
%ifidn ROUTINE, carrier_detect
    and ax, strict word 0x80
%else
    and ax, strict word 0x10
%endif
    ret
