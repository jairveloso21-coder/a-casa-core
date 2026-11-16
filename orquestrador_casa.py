import argparse, hashlib, json, re, shutil, subprocess, sys, zipfile
from datetime import datetime
from pathlib import Path

PROIBIDOS = ["// resto do codigo", "# resto do codigo", "# implementar", "// todo", "# todo", "fixme", "raise notimplementederror"]
ADB_PATH = r"C:\Users\jairv\AppData\Local\Microsoft\WinGet\Packages\Genymobile.scrcpy_Microsoft.Winget.Source_8wekyb3d8bbwe\scrcpy-win64-v4.1\adb.exe"

def extrair_json_bruto(texto: str) -> dict:
    texto = texto.strip()
    bloco = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", texto, re.DOTALL)
    if bloco:
        texto = bloco.group(1)
    else:
        inicio, fim = texto.find("{"), texto.rfind("}")
        if inicio != -1 and fim != -1 and fim > inicio:
            texto = texto[inicio:fim+1]
    return json.loads(texto)

def hash_logico(texto: str) -> str:
    linhas = [re.sub(r"\s+", " ", l.strip()) for l in texto.splitlines() if l.strip() and not l.strip().startswith(("#", "//"))]
    return hashlib.sha256("\n".join(linhas).encode("utf-8")).hexdigest()

def auditar_e_testar_mobile(bin_path: Path) -> tuple[bool, str, str]:
    if not bin_path.exists():
        return False, f"Binario nao gerado: {bin_path}", ""
    cab = bin_path.read_bytes()[:64]
    
    # 1. Binario nativo ELF (ARM 32-bit)
    if cab.startswith(b"\x7fELF"):
        classe_bits = cab[4]
        maquina = int.from_bytes(cab[18:20], "little")
        if classe_bits != 1 or maquina != 40:
            return False, f"ELF invalido (classe={classe_bits}, machine={hex(maquina)}). O celular AFTKM exige ARM 32-bit (armeabi-v7a).", ""
        
        # Execucao real no celular AFTKM via ADB
        check_adb = subprocess.run(f'"{ADB_PATH}" devices', shell=True, capture_output=True, text=True)
        if "\tdevice" in check_adb.stdout:
            remoto = f"/data/local/tmp/{bin_path.name}"
            subprocess.run(f'"{ADB_PATH}" push "{bin_path}" "{remoto}"', shell=True, capture_output=True)
            subprocess.run(f'"{ADB_PATH}" shell chmod 755 "{remoto}"', shell=True, capture_output=True)
            exec_adb = subprocess.run(f'"{ADB_PATH}" shell "{remoto}"', shell=True, capture_output=True, text=True, timeout=15)
            if exec_adb.returncode != 0:
                return False, f"Binario ELF ARM32 compilou, mas falhou ao rodar no celular AFTKM: {exec_adb.stderr}", ""
            return True, "ELF ARM 32-bit autenticado e executado no hardware AFTKM.", exec_adb.stdout.strip()
        return True, "ELF ARM 32-bit autenticado (ADB offline para teste em hardware).", ""

    # 2. Pacote Android APK
    if cab.startswith(b"PK\x03\x04") and bin_path.suffix.lower() == ".apk":
        with zipfile.ZipFile(bin_path, "r") as z:
            libs = [f for f in z.namelist() if f.startswith("lib/")]
            if libs and not any(f.startswith("lib/armeabi-v7a/") for f in libs):
                return False, "APK sem pasta lib/armeabi-v7a/ para o dispositivo AFTKM.", ""
        return True, "APK armeabi-v7a autenticado.", ""

    return True, "Artefato verificado.", ""

def gerar_mensagem_retorno(res: dict) -> str:
    if res["status"] == "HOMOLOGADO_SUCESSO":
        return (
            f"[A CASA - CERTIFICADO DE HOMOLOGAÇÃO PERC v8.0]\n"
            f"OS: {res.get('id_os')} | Hash Lógico: {res.get('hash')}\n"
            f"Auditoria Binária: {res.get('binario')}\n"
            f"Saída em Hardware/Teste: {res.get('validacao')}\n"
            f"Status: APROVADO E VALIDADO. ChatGPT, pode realizar a auditoria final."
        )
    return (
        f"[A CASA - REJEIÇÃO AUTOMÁTICA PERC v8.0]\n"
        f"Status: {res['status']}\n"
        f"Motivo/Log de Erro:\n{res.get('motivo') or res.get('stderr')}\n\n"
        f"QWEN: Corrija o erro acima respeitando estritamente o PROTOCOLO_PERC_V5.md e devolva o JSON completo atualizado."
    )

def processar_texto_ou_arquivo(entrada: str) -> dict:
    p = Path(entrada)
    raw = p.read_text(encoding="utf-8-sig") if p.exists() else entrada
    try:
        dados = extrair_json_bruto(raw)
    except Exception as e:
        res = {"status": "REJEITADO_JSON", "motivo": f"JSON invalido na resposta da Qwen: {e}"}
        res["prompt_retorno"] = gerar_mensagem_retorno(res)
        return res

    alvo = dados.get("alvo", "")
    dest = Path(dados.get("arquivo_destino", ""))
    bin_out = Path(dados["binario_gerado"]) if dados.get("binario_gerado") else None
    cod = dados.get("codigo_completo", "")
    build = dados.get("comando_build", "")
    val = dados.get("comando_validacao", "")

    if not dest or not cod or not build:
        res = {"status": "REJEITADO_CONTRATO", "motivo": "Campos obrigatorios ausentes no JSON."}
        res["prompt_retorno"] = gerar_mensagem_retorno(res)
        return res

    if len(cod.splitlines()) < 5 or any(t in cod.lower() for t in PROIBIDOS):
        res = {"status": "REJEITADO_PREGUICA", "motivo": "Codigo truncado ou contem placeholders proibidos (TODO, ..., resto do codigo)."}
        res["prompt_retorno"] = gerar_mensagem_retorno(res)
        return res

    h_novo = hash_logico(cod)
    if dest.exists() and h_novo == hash_logico(dest.read_text(encoding="utf-8", errors="ignore")):
        res = {"status": "REJEITADO_CLONE", "motivo": "Codigo logicamente identico ao anterior (SHA-256 igual)."}
        res["prompt_retorno"] = gerar_mensagem_retorno(res)
        return res

    if alvo == "ANDROID_ARMV7" and "arm64-v8a" in cod.lower() and "armeabi-v7a" not in cod.lower():
        res = {"status": "REJEITADO_ARQ", "motivo": "Codigo configurado para arm64-v8a. O alvo AFTKM exige armeabi-v7a."}
        res["prompt_retorno"] = gerar_mensagem_retorno(res)
        return res

    bkp = None
    if dest.exists():
        bkp_dir = dest.parent / ".casa_sandbox"
        bkp_dir.mkdir(parents=True, exist_ok=True)
        bkp = bkp_dir / f"{dest.name}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
        shutil.copy2(dest, bkp)

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(cod, encoding="utf-8")

    p_build = subprocess.run(build, shell=True, capture_output=True, text=True)
    if p_build.returncode != 0:
        if bkp: shutil.copy2(bkp, dest)
        res = {"status": "FALHA_BUILD_ROLLBACK", "stderr": "\n".join((p_build.stderr or p_build.stdout).splitlines()[-30:])}
        res["prompt_retorno"] = gerar_mensagem_retorno(res)
        return res

    msg_bin, saida_adb = "N/A", ""
    if bin_out and alvo == "ANDROID_ARMV7":
        ok, msg_bin, saida_adb = auditar_e_testar_mobile(bin_out)
        if not ok:
            if bkp: shutil.copy2(bkp, dest)
            res = {"status": "REJEITADO_BINARIO_ROLLBACK", "motivo": msg_bin}
            res["prompt_retorno"] = gerar_mensagem_retorno(res)
            return res

    saida_val = saida_adb if saida_adb else "OK"
    if val:
        p_val = subprocess.run(val, shell=True, capture_output=True, text=True)
        if p_val.returncode != 0:
            if bkp: shutil.copy2(bkp, dest)
            res = {"status": "FALHA_TESTE_ROLLBACK", "stderr": "\n".join((p_val.stderr or p_val.stdout).splitlines()[-30:])}
            res["prompt_retorno"] = gerar_mensagem_retorno(res)
            return res
        saida_val = "\n".join(p_val.stdout.splitlines()[-10:])

    res = {
        "status": "HOMOLOGADO_SUCESSO",
        "id_os": dados.get("id_os", "N/A"),
        "hash": h_novo[:16],
        "binario": msg_bin,
        "validacao": saida_val
    }
    res["prompt_retorno"] = gerar_mensagem_retorno(res)
    return res

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada", help="Caminho de arquivo JSON ou string bruta")
    args = ap.parse_args()
    resultado = processar_texto_ou_arquivo(args.entrada)
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
    sys.exit(0 if resultado["status"] == "HOMOLOGADO_SUCESSO" else 1)

