// Copyright 2022 The Go Authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

#include "../../../../../runtime/textflag.h"

TEXT asmtest(SB),DUPOK|NOSPLIT,$0
lable1:
	BFPT	1(PC)			// 00050048
	BFPT	lable1	// BFPT 2	//1ffdff4b

lable2:
	BFPF	1(PC)			// 00040048
	BFPF	lable2	// BFPF 4 	// 1ffcff4b

	JMP	foo(SB)			// 00100050
	JMP	(R4)			// 8000004c
	JMP	1(PC)			// 00040058
	MOVW	$65536, R4		// 04020014
	MOVW	$4096, R4		// 24000014
	MOVV	$65536, R4		// 04020014
	MOVV	$4096, R4		// 24000014
	MOVW	R4, R5			// 85001700
	MOVV	R4, R5			// 85001500
	MOVBU	R4, R5			// 85fc4303
	SUB	R4, R5, R6		// a6101100
	SUBV	R4, R5, R6		// a6901100
	ADD	R4, R5, R6		// a6101000
	ADDV	R4, R5, R6		// a6901000
	AND	R4, R5, R6		// a6901400
	SUB	R4, R5			// a5101100
	SUBV	R4, R5			// a5901100
	ADD	R4, R5			// a5101000
	ADDV	R4, R5			// a5901000
	AND	R4, R5			// a5901400
	NEGW	R4, R5			// 05101100
	NEGV	R4, R5			// 05901100
	SLL	R4, R5			// a5101700
	SLL	R4, R5, R6		// a6101700
	SRL	R4, R5			// a5901700
	SRL	R4, R5, R6	 	// a6901700
	SRA	R4, R5			// a5101800
	SRA	R4, R5, R6	 	// a6101800
	SLLV	R4, R5			// a5901800
	SLLV	R4, R5, R6		// a6901800
	CLO	R4, R5			// 85100000
	CLZ	R4, R5			// 85140000
	ADDF	F4, F5			// a5900001
	ADDF	F4, R5, F6		// a6900001
	CMPEQF	F4, R5			// a010120c
	ABSF	F4, F5			// 85041401
	MOVVF	F4, F5			// 85181d01
	MOVF	F4, F5			// 85941401
	MOVD	F4, F5			// 85981401
	MOVW	R4, result+16(FP)	// 64608029
	MOVWU	R4, result+16(FP)	// 64608029
	MOVV	R4, result+16(FP)	// 6460c029
	MOVB	R4, result+16(FP)	// 64600029
	MOVBU	R4, result+16(FP)	// 64600029
	MOVWL	R4, result+16(FP)	// 6460002f
	MOVVL	R4, result+16(FP)	// 6460802f
	MOVW	R4, 1(R5)		// a4048029
	MOVWU	R4, 1(R5)		// a4048029
	MOVV	R4, 1(R5)		// a404c029
	MOVB	R4, 1(R5)		// a4040029
	MOVBU	R4, 1(R5)		// a4040029
	MOVWL	R4, 1(R5)		// a404002f
	MOVVL	R4, 1(R5)		// a404802f
	SC	R4, 1(R5)		// a4040021
	SCV	R4, 1(R5)		// a4040023
	MOVW	y+8(FP), R4		// 64408028
	MOVWU	y+8(FP), R4		// 6440802a
	MOVV	y+8(FP), R4		// 6440c028
	MOVB	y+8(FP), R4		// 64400028
	MOVBU	y+8(FP), R4		// 6440002a
	MOVWL	y+8(FP), R4		// 6440002e
	MOVVL	y+8(FP), R4		// 6440802e
	MOVW	1(R5), R4		// a4048028
	MOVWU	1(R5), R4		// a404802a
	MOVV	1(R5), R4		// a404c028
	MOVB	1(R5), R4		// a4040028
	MOVBU	1(R5), R4		// a404002a
	MOVWL	1(R5), R4		// a404002e
	MOVVL	1(R5), R4		// a404802e
	LL	1(R5), R4		// a4040020
	LLV	1(R5), R4		// a4040022
	MOVW	$4(R4), R5		// 8510c002
	MOVV	$4(R4), R5		// 8510c002
	MOVW	$-1, R4			// 04fcff02
	MOVV	$-1, R4			// 04fcff02
	MOVW	$1, R4			// 0404c002
	MOVV	$1, R4			// 0404c002
	ADD	$-1, R4, R5		// 85fcbf02
	ADD	$-1, R4			// 84fcbf02
	ADDV	$-1, R4, R5		// 85fcff02
	ADDV	$-1, R4			// 84fcff02
	AND	$1, R4, R5		// 85044003
	AND	$1, R4			// 84044003
	SLL	$4, R4, R5		// 85904000
	SLL	$4, R4			// 84904000
	SRL	$4, R4, R5		// 85904400
	SRL	$4, R4			// 84904400
	SRA	$4, R4, R5		// 85904800
	SRA	$4, R4			// 84904800
	SLLV	$4, R4, R5		// 85104100
	SLLV	$4, R4			// 84104100
	SYSCALL				// 00002b00
	BEQ	R4, R5, 1(PC)		// 85040058
	BEQ	R4, 1(PC)		// 80040058
	BLTU	R4, 1(PC)		// 80040068
	MOVW	y+8(FP), F4		// 6440002b
	MOVF	y+8(FP), F4		// 6440002b
	MOVD	y+8(FP), F4		// 6440802b
	MOVW	1(F5), F4		// a404002b
	MOVF	1(F5), F4		// a404002b
	MOVD	1(F5), F4		// a404802b
	MOVW	F4, result+16(FP)	// 6460402b
	MOVF	F4, result+16(FP)	// 6460402b
	MOVD	F4, result+16(FP)	// 6460c02b
	MOVW	F4, 1(F5)		// a404402b
	MOVF	F4, 1(F5)		// a404402b
	MOVD	F4, 1(F5)		// a404c02b
	MOVW	R4, F5			// 85a41401
	MOVW	F4, R5			// 85b41401
	MOVV	R4, F5			// 85a81401
	MOVV	F4, R5			// 85b81401
	WORD	$74565			// 45230100
	BREAK	R4, result+16(FP)	// 64600006
	BREAK	R4, 1(R5)		// a4040006
	BREAK				// 00002a00
	UNDEF				// 00002a00

	// mul
	MUL	R4, R5	  		// a5101c00
	MUL	R4, R5, R6	  	// a6101c00
	MULV	R4, R5	   		// a5901d00
	MULV	R4, R5, R6	   	// a6901d00
	MULVU	R4, R5			// a5901d00
	MULVU	R4, R5, R6		// a6901d00
	MULHV	R4, R5			// a5101e00
	MULHV	R4, R5, R6		// a6101e00
	MULHVU	R4, R5			// a5901e00
	MULHVU	R4, R5, R6	 	// a6901e00
	REMV	R4, R5	   		// a5902200
	REMV	R4, R5, R6	   	// a6902200
	REMVU	R4, R5			// a5902300
	REMVU	R4, R5, R6		// a6902300
	DIVV	R4, R5			// a5102200
	DIVV	R4, R5, R6	   	// a6102200
	DIVVU	R4, R5	 		// a5102300
	DIVVU	R4, R5, R6		// a6102300

	MOVH	R4, result+16(FP)	// 64604029
	MOVH	R4, 1(R5)		// a4044029
	MOVH	y+8(FP), R4		// 64404028
	MOVH	1(R5), R4		// a4044028
	MOVHU	R4, R5			// 8500cf00
	MOVHU	R4, result+16(FP)	// 64604029
	MOVHU	R4, 1(R5)		// a4044029
	MOVHU	y+8(FP), R4		// 6440402a
	MOVHU	1(R5), R4		// a404402a
	MULU	R4, R5	   		// a5101c00
	MULU	R4, R5, R6		// a6101c00
	MULH	R4, R5	   		// a5901c00
	MULH	R4, R5, R6	   	// a6901c00
	MULHU	R4, R5			// a5101d00
	MULHU	R4, R5, R6		// a6101d00
	REM	R4, R5	  		// a5902000
	REM	R4, R5, R6	  	// a6902000
	REMU	R4, R5	   		// a5902100
	REMU	R4, R5, R6	   	// a6902100
	DIV	R4, R5	  		// a5102000
	DIV	R4, R5, R6	  	// a6102000
	DIVU	R4, R5	   		// a5102100
	DIVU	R4, R5, R6	   	// a6102100
	SRLV	R4, R5 			// a5101900
	SRLV	R4, R5, R6 		// a6101900
	SRLV	$4, R4, R5		// 85104500
	SRLV	$4, R4			// 84104500
	SRLV	$32, R4, R5 		// 85804500
	SRLV	$32, R4			// 84804500

	MOVFD	F4, F5			// 85241901
	MOVDF	F4, F5			// 85181901
	MOVWF	F4, F5			// 85101d01
	MOVFW	F4, F5			// 85041b01
	MOVWD	F4, F5			// 85201d01
	MOVDW	F4, F5			// 85081b01
	NEGF	F4, F5			// 85141401
	NEGD	F4, F5			// 85181401
	ABSD	F4, F5			// 85081401
	TRUNCDW	F4, F5			// 85881a01
	TRUNCFW	F4, F5			// 85841a01
	SQRTF	F4, F5			// 85441401
	SQRTD	F4, F5			// 85481401

	DBAR	 			// 00007238
	NOOP	 			// 00004003

	MOVWR	R4, result+16(FP) 	// 6460402f
	MOVWR	R4, 1(R5) 		// a404402f
	MOVWR	y+8(FP), R4 		// 6440402e
	MOVWR	1(R5), R4 		// a404402e

	CMPGTF	F4, R5 			// a090110c
	CMPGTD	F4, R5 			// a090210c
	CMPGEF	F4, R5			// a090130c
	CMPGED	F4, R5			// a090230c
	CMPEQD	F4, R5			// a010220c
