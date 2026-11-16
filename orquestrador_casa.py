import argparse, hashlib, json, re, shutil, subprocess, sys, zipfile
from datetime import datetime
from pathlib import Path

PROIBIDOS = ["// resto do codigo", "# resto do codigo", "# implementar", "// todo", "# todo", "fixme", "raise notimplementederror"]
ADB_PATH = r"C:\Users\jairv\AppData\Local\Microsoft\WinGet\Packages\Genymobile.scrcpy_Microsoft.Winget.Source_8wekyb3d8bbwe\scrcpy-win64-v4.1\adb.exe"
PLANTA_PATH = Path(r"C:\Users\jairv\Desktop\casa core homologação\PLANTA_CASA.json")

def extrair_json_bruto(texto: str) -> dict:
    texto = texto.strip()
    bloco = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", texto, re.DOTALL)
    if bloco:
        texto = bloco.group(1)
    else:
        i, f = texto.find("{"), texto.rfind("}")
        if i != -1 and f > i: texto = texto[i:f+1]
    return json.loads(texto)

def hash_logico(texto: str) -> str:
    linhas = [re.sub(r"\s+", " ", l.strip()) for l in texto.splitlines() if l.strip() and not l.strip().startswith(("#", "//"))]
    return hashlib.sha256("\n".join(linhas).encode("utf-8")).hexdigest()

def obter_alvo_adb(alvo: str) -> tuple[str, str]:
    if not PLANTA_PATH.exists(): return "", ""
    planta = json.loads(PLANTA_PATH.read_text(encoding="utf-8-sig"))
    chave = "celular_principal" if alvo == "CELULAR_GARNED" else "firestick_tv"
    dev = planta.get("dispositivos", {}).get(chave, {})
    return dev.get("serial_adb", ""), dev.get("arquitetura", "")

def auditar_mobile(bin_path: Path, alvo: str) -> tuple[bool, str, str]:
    if not bin_path.exists(): return False, f"Binario nao gerado: {bin_path}", ""
    serial, arch = obter_alvo_adb(alvo)
    cab = bin_path.read_bytes()[:64]
    if cab.startswith(b"\x7fELF"):
        bits, maq = cab[4], int.from_bytes(cab[18:20], "little")
        if arch == "armeabi-v7a" and (bits != 1 or maq != 40): return False, f"ELF invalido para {alvo}: exige ARM 32-bit.", ""
        if arch == "arm64-v8a" and (bits != 2 or maq != 183): return False, f"ELF invalido para {alvo}: exige ARM 64-bit.", ""
        chk = subprocess.run(f'"{ADB_PATH}" devices', shell=True, capture_output=True, text=True)
        if serial and serial in chk.stdout:
            rem = f"/data/local/tmp/{bin_path.name}"
            subprocess.run(f'"{ADB_PATH}" -s {serial} push "{bin_path}" "{rem}"', shell=True, capture_output=True)
            subprocess.run(f'"{ADB_PATH}" -s {serial} shell chmod 755 "{rem}"', shell=True, capture_output=True)
            ex = subprocess.run(f'"{ADB_PATH}" -s {serial} shell "{rem}"', shell=True, capture_output=True, text=True, timeout=15)
            if ex.returncode != 0: return False, f"Erro ao rodar em {alvo}: {ex.stderr}", ""
            return True, f"Executado com sucesso em {alvo} ({serial}).", ex.stdout.strip()
        return True, f"Binario autenticado para {alvo} (offline no ADB).", ""
    if cab.startswith(b"PK\x03\x04") and bin_path.suffix.lower() == ".apk":
        with zipfile.ZipFile(bin_path, "r") as z:
            libs = [f for f in z.namelist() if f.startswith("lib/")]
            if libs and arch and not any(f.startswith(f"lib/{arch}/") for f in libs):
                return False, f"APK sem lib/{arch}/ exigida por {alvo}.", ""
        return True, f"APK {alvo} ({arch}) autenticado.", ""
    return True, "Artefato OK.", ""

def msg_retorno(res: dict) -> str:
    if res["status"] == "HOMOLOGADO_SUCESSO":
        return f"[A CASA - HOMOLOGADO PERC v8.2]\nOS: {res.get('id_os')} | Alvo: {res.get('alvo')} | Hash: {res.get('hash')}\nAuditoria: {res.get('binario')}\nSaida: {res.get('validacao')}\nStatus: APROVADO. ChatGPT, pode auditar."
    return f"[A CASA - REJEITADO PERC v8.2]\nStatus: {res['status']}\nErro:\n{res.get('motivo') or res.get('stderr')}\n\nQWEN: Corrija e devolva o JSON completo."

def processar_texto_ou_arquivo(entrada: str) -> dict:
    p = Path(entrada)
    raw = p.read_text(encoding="utf-8-sig") if p.exists() else entrada
    try: dados = extrair_json_bruto(raw)
    except Exception as e:
        r = {"status": "REJEITADO_JSON", "motivo": str(e)}
        r["prompt_retorno"] = msg_retorno(r)
        return r
    alvo, dest = dados.get("alvo", ""), Path(dados.get("arquivo_destino", ""))
    bin_out = Path(dados["binario_gerado"]) if dados.get("binario_gerado") else None
    cod, build, val = dados.get("codigo_completo", ""), dados.get("comando_build", ""), dados.get("comando_validacao", "")
    if not dest or not cod or not build or len(cod.splitlines()) < 5 or any(t in cod.lower() for t in PROIBIDOS):
        r = {"status": "REJEITADO_CONTRATO", "motivo": "Codigo ausente, truncado ou com placeholders proibidos."}
        r["prompt_retorno"] = msg_retorno(r)
        return r
    h_novo = hash_logico(cod)
    if dest.exists() and h_novo == hash_logico(dest.read_text(encoding="utf-8", errors="ignore")):
        r = {"status": "REJEITADO_CLONE", "motivo": "Codigo identico ao anterior (SHA-256 igual)."}
        r["prompt_retorno"] = msg_retorno(r)
        return r
    bkp = None
    if dest.exists():
        bdir = dest.parent / ".casa_sandbox"
        bdir.mkdir(parents=True, exist_ok=True)
        bkp = bdir / f"{dest.name}.{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
        shutil.copy2(dest, bkp)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(cod, encoding="utf-8")
    pb = subprocess.run(build, shell=True, capture_output=True, text=True)
    if pb.returncode != 0:
        if bkp: shutil.copy2(bkp, dest)
        r = {"status": "FALHA_BUILD_ROLLBACK", "stderr": "\n".join((pb.stderr or pb.stdout).splitlines()[-30:])}
        r["prompt_retorno"] = msg_retorno(r)
        return r
    m_bin, s_adb = "N/A", ""
    if bin_out and alvo in ("CELULAR_GARNED", "FIRESTICK_AFTKM"):
        ok, m_bin, s_adb = auditar_mobile(bin_out, alvo)
        if not ok:
            if bkp: shutil.copy2(bkp, dest)
            r = {"status": "REJEITADO_BINARIO_ROLLBACK", "motivo": m_bin}
            r["prompt_retorno"] = msg_retorno(r)
            return r
    s_val = s_adb if s_adb else "OK"
    if val:
        pv = subprocess.run(val, shell=True, capture_output=True, text=True)
        if pv.returncode != 0:
            if bkp: shutil.copy2(bkp, dest)
            r = {"status": "FALHA_TESTE_ROLLBACK", "stderr": "\n".join((pv.stderr or pv.stdout).splitlines()[-30:])}
            r["prompt_retorno"] = msg_retorno(r)
            return r
        s_val = "\n".join(pv.stdout.splitlines()[-10:])
    r = {"status": "HOMOLOGADO_SUCESSO", "id_os": dados.get("id_os", "N/A"), "alvo": alvo, "hash": h_novo[:16], "binario": m_bin, "validacao": s_val}
    r["prompt_retorno"] = msg_retorno(r)
    return r

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("entrada")
    res = processar_texto_ou_arquivo(ap.parse_args().entrada)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    sys.exit(0 if res["status"] == "HOMOLOGADO_SUCESSO" else 1)
    args = ap.parse_args()
    if args.autonomo:
        p = Path(args.entrada)
        texto_os = p.read_text(encoding="utf-8-sig") if p.exists() else args.entrada
        res = executar_loop_autonomo(texto_os, modelo=args.modelo)
    else:
        res = processar_texto_ou_arquivo(args.entrada)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    sys.exit(0 if res["status"] == "HOMOLOGADO_SUCESSO" else 1)

