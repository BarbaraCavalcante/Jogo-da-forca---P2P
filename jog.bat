@echo off
title Jogo da Forca P2P

REM ==============================
REM  Escolher Modo
REM ==============================
echo ==============================
echo  Jogo da Forca P2P (TCP/UDP)
echo ==============================
set /p modo=Digite S para Servidor ou C para Cliente: 

if /I "%modo%"=="S" (
    set modo_arg=servidor
) else (
    set modo_arg=cliente
)

REM ==============================
REM  Perguntar IP
REM ==============================
set /p ip=Digite o IP (para servidor, use seu IP local): 

REM ==============================
REM  Perguntar Porta
REM ==============================
set /p porta=Digite a Porta (ex: 5555): 

REM ==============================
REM  Perguntar Protocolo
REM ==============================
set /p protocolo=Digite o protocolo (TCP ou UDP): 

REM ==============================
REM  Executar o jogo com os parâmetros
REM ==============================
python main.py --modo %modo_arg% --ip %ip% --porta %porta% --protocolo %protocolo%

pause
