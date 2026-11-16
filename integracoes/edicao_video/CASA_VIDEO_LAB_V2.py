#!/usr/bin/env python3
"""CASA Video Lab V2: edit original gameplay footage into vertical social shorts.
No external licensed audio, no remote downloads, deterministic source timelines.
Usage: python casa_video_lab_v2.py [tekken|zelda|boss|all]
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import subprocess, json, hashlib, os, sys, math, shutil, time

SCRIPT_DIR=Path(__file__).resolve().parent
ROOT=Path(os.environ.get("CASA_VIDEO_OUTPUT_DIR",str(SCRIPT_DIR/"outputs"))).resolve()
ROOT.mkdir(parents=True,exist_ok=True)
SOURCE_DIR=Path(os.environ.get("CASA_VIDEO_SOURCE_DIR",str(SCRIPT_DIR/"sources"))).resolve()
W,H,FPS=720,1280,30
def choose_font(primary):
    candidate=os.environ.get("CASA_VIDEO_FONT")
    if candidate and Path(candidate).exists():return candidate
    paths=[
        f"/usr/share/fonts/truetype/lato/Lato-{primary}.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf"
    ]
    for font in paths:
        if Path(font).exists():return font
    raise RuntimeError("No supported font found; set CASA_VIDEO_FONT")
FONT=choose_font("Black")
REG=choose_font("Semibold")
SOURCES={
 "tekken_a": SOURCE_DIR/"20261110_093952_00312013.mp4",
 "tekken_b": SOURCE_DIR/"20261110_154545_00477552.webm",
 "boss": SOURCE_DIR/"20261115_115257_00612931.webm",
 "zelda": SOURCE_DIR/"20261116_172215_00032424.webm",
}
STORIES={
 "tekken":{
    "title":"TEKKEN 8 — 2 ROUNDS, 1 ESCOLHA",
    "out":"TEKKEN8_V2_DOIS_COMBOS.mp4",
    "accent":(253,85,77),
    "segments":[
      ("tekken_b",4.25,1.60,"wide",0.50),
      ("tekken_a",0.65,2.55,"wide",0.49),
      ("tekken_a",5.55,2.60,"wide",0.52),
      ("tekken_a",9.30,3.35,"wide",0.52),
      ("tekken_b",0.55,2.70,"wide",0.49),
      ("tekken_b",7.65,2.45,"wide",0.52),
      ("tekken_b",11.25,2.65,"wide",0.51),
    ],
    "titles":[
       ("2 COMBOS. QUAL VENCE?",0,2.2,45,148,"top"),
       ("COMBO 01",2.3,8.9,39,156,"top"),
       ("COMBO 02",10.1,17.75,39,156,"top"),
       ("QUAL FOI MELHOR? 1 OU 2?",15.75,17.90,39,1024,"bottom")
    ],
    "eyebrow":"TEKKEN 8  /  DUEL",
    "caption":"DOIS COMBOS DE TEKKEN 8. SÓ UM LEVA A MELHOR. 🥊🔥 Qual você escolhe: 1 ou 2?",
    "tags":["#Tekken8","#FGC","#Gameplay","#Games","#Shorts"]
 },
 "zelda":{
    "title":"ZELDA — O SALTO QUE NÃO ACABA",
    "out":"ZELDA_V2_SALTO_SEM_FIM.mp4",
    "accent":(78,239,203),
    "segments":[
      ("zelda",157.80,2.55,"full",0.31),
      ("zelda",113.10,3.40,"wide",0.52),
      ("zelda",118.35,3.40,"full",0.52),
      ("zelda",140.30,3.40,"full",0.52),
      ("zelda",153.10,3.20,"full",0.52),
      ("zelda",170.40,5.30,"wide",0.52),
    ],
    "titles":[
       ("ESSE SALTO PARECE INFINITO",0,2.55,44,141,"top"),
       ("OLHA ONDE TUDO COMEÇOU",2.55,5.95,42,147,"top"),
       ("A VISTA FICA CADA VEZ MELHOR",12.75,16.2,38,148,"top"),
       ("VOCÊ PULARIA?",18.8,21.20,43,1020,"bottom")
    ],
    "eyebrow":"ZELDA  /  SKY DIVE",
    "caption":"VOCÊ TERIA CORAGEM DE PULAR? ☁️ 🏹 O final dessa queda é surreal.",
    "tags":["#Zelda","#TearsOfTheKingdom","#Nintendo","#Gameplay","#Shorts"]
 },
 "boss":{
    "title":"BOSS FIGHT — REPLAY DO GOLPE FINAL",
    "out":"BOSS_V2_REPLAY_FINAL.mp4",
    "accent":(255,187,66),
    "segments":[
      ("boss",5.25,1.65,"wide",0.54),
      ("boss",0.65,1.70,"wide",0.51),
      ("boss",2.55,2.25,"wide",0.50),
      ("boss",4.80,2.10,"wide",0.53),
      ("boss",12.40,2.48,"wide",0.51),
    ],
    "titles":[
       ("ESSE FINAL É INSANO",0,1.7,48,148,"top"),
       ("OLHA A VIRADA...",1.75,5.3,47,155,"top"),
       ("O ÚLTIMO GOLPE",6.05,9.9,45,148,"top"),
       ("NOTA DE 0 A 10?",8.25,10.18,43,1033,"bottom")
    ],
    "eyebrow":"BOSS FIGHT  /  FINISHER",
    "caption":"DO CAOS AO GOLPE FINAL! ⚔️🔥 Quanto vale essa finalização de 0 a 10?",
    "tags":["#BossFight","#Gameplay","#Gaming","#Games","#Shorts"]
 }
}
def sha256(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()
def probe(p):
    r=subprocess.run(["ffprobe","-v","error","-show_format","-show_streams","-of","json",str(p)],capture_output=True,text=True,check=True)
    d=json.loads(r.stdout); ss=d['streams']
    v=next(s for s in ss if s['codec_type']=='video')
    a=next((s for s in ss if s['codec_type']=='audio'),{})
    return {"duration":float(d['format']['duration']), "width":v['width'],"height":v['height'],"v_codec":v['codec_name'],"a_codec":a.get('codec_name'),"fps":v.get("avg_frame_rate")}
def visual_overlay(story,key):
    """Subtle gradients and compact design; no oversized black banners."""
    im=Image.new("RGBA",(W,H),(0,0,0,0))
    pix=im.load()
    for y in range(H):
        if y < 425:
            strength=0.43*(1-y/425)**1.2+0.02
        elif y > 900:
            strength=0.025+0.33*((y-900)/(H-900))**1.3
        else:
            strength=0.008
        alpha=int(max(0,min(1,strength))*255)
        for x in range(W):
            pix[x,y]=(4,8,14,alpha)
    d=ImageDraw.Draw(im)
    c=story['accent']
    d.rounded_rectangle([49,68,134,74],radius=3,fill=(*c,255))
    font=ImageFont.truetype(REG,20)
    d.text((49,91),story['eyebrow'],font=font,fill=(232,238,246,245))
    d.line([(49,1241),(671,1241)],fill=(255,255,255,94),width=2)
    d.rounded_rectangle([49,1236,151,1246],radius=5,fill=(*c,255))
    path=ROOT/f"{key}_overlay.png";im.save(path);return path
def quote_path(p):return str(p).replace("\\","/")
def draw_text_filters(story,key,duration):
    output=[]
    for i,(label,start,end,size,y,pos) in enumerate(story['titles']):
        # Clamp to available timeline to avoid overlay at the very end.
        end=min(float(end),duration-.08)
        start=float(start)
        txt=ROOT/f"{key}_text_{i}.txt";txt.write_text(label,encoding="utf-8")
        # Keep the text inside 720px with 47px readable type.
        output.append(
        f"drawtext=fontfile='{FONT}':textfile='{quote_path(txt)}':"
        f"x=(w-text_w)/2:y={y}:fontsize={size}:fontcolor=white:"
        f"borderw=2:bordercolor=black@0.45:shadowcolor=black@0.45:shadowx=1:shadowy=3:"
        f"enable='between(t,{start:.2f},{end:.2f})'"
        )
    return output
def build(name):
    story=STORIES[name];output=ROOT/story["out"]
    segs=story["segments"];duration=sum(s[2] for s in segs)
    assets=visual_overlay(story,name)
    args=["ffmpeg","-hide_banner","-loglevel","warning","-nostdin","-y"]
    for key,t,d,mode,center in segs:
        assert SOURCES[key].exists(),f"Missing source: {SOURCES[key]}"
        args+=["-ss",f"{t:.3f}","-t",f"{d:.3f}","-i",str(SOURCES[key])]
    args+=["-loop","1","-framerate",str(FPS),"-i",str(assets)]
    fc=[]
    for i,(key,start,dur,mode,center) in enumerate(segs):
        # VFR source and 59.94 -> all outputs stable 30 fps.
        # Preserve a wide fighting/gameplay area; for skydive use full-bleed vertical.
        if mode=="wide":
            fc.append(
              f"[{i}:v]fps={FPS},setsar=1,split=2[bg{i}][fg{i}];"
              f"[bg{i}]crop=iw*0.79:ih*0.62:x=iw*0.105:y=ih*0.19,"
              f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=bicubic,"
              f"crop={W}:{H},boxblur=27:3,eq=brightness=-0.045:saturation=1.0[bk{i}];"
              f"[fg{i}]scale={W}:585:force_original_aspect_ratio=increase:flags=lanczos,"
              f"crop={W}:585:x='max(0,min(iw-ow,iw*{center:.3f}-ow/2))':y='(ih-oh)/2',"
              f"eq=contrast=1.045:saturation=1.12[main{i}];"
              f"[bk{i}][main{i}]overlay=0:333:shortest=1,"
              f"drawbox=x=0:y=331:w={W}:h=3:color=white@0.18:t=fill,"
              f"drawbox=x=0:y=918:w={W}:h=3:color=white@0.18:t=fill,"
              f"trim=duration={dur:.3f},setpts=PTS-STARTPTS,format=yuv420p,setsar=1[v{i}]"
            )
        else:
            fc.append(
              f"[{i}:v]fps={FPS},setsar=1,"
              f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
              f"crop={W}:{H}:x='max(0,min(iw-ow,iw*{center:.3f}-ow/2))':y='(ih-oh)/2',"
              f"eq=contrast=1.04:saturation=1.08,"
              f"trim=duration={dur:.3f},setpts=PTS-STARTPTS,format=yuv420p,setsar=1[v{i}]"
            )
        fc.append(
            f"[{i}:a]aformat=sample_rates=48000:channel_layouts=stereo,"
            f"atrim=duration={dur:.3f},asetpts=PTS-STARTPTS,"
            f"afade=t=in:st=0:d=0.025,afade=t=out:st={max(0,dur-.035):.3f}:d=0.035[a{i}]"
        )
    streams=''.join(f"[v{i}][a{i}]" for i in range(len(segs)))
    fc.append(f"{streams}concat=n={len(segs)}:v=1:a=1[vcat][acat]")
    over_idx=len(segs)
    videofx=f"[vcat][{over_idx}:v]overlay=0:0:shortest=1,format=yuv420p"
    for fx in draw_text_filters(story,name,duration):
        videofx += ","+fx
    videofx += "[vout]"
    fc.append(videofx)
    fc.append(f"[acat]highpass=f=55,acompressor=threshold=-18dB:ratio=2.1:attack=7:release=120,"
              f"loudnorm=I=-16:TP=-1.5:LRA=11,"
              f"afade=t=out:st={max(0,duration-.20):.3f}:d=0.20[aout]")
    filter_path=ROOT/f"{name}_filter_complex.txt"
    filter_path.write_text(";\n".join(fc),encoding="utf-8")
    args+=["-filter_complex",";\n".join(fc),"-map","[vout]","-map","[aout]",
           "-c:v","libx264","-preset","veryfast","-crf","20","-pix_fmt","yuv420p",
           "-profile:v","high","-level:v","3.1","-r",str(FPS),"-movflags","+faststart",
           "-c:a","aac","-b:a","192k","-ar","48000","-ac","2","-shortest",str(output)]
    t0=time.time()
    run=subprocess.run(args,text=True,capture_output=True)
    (ROOT/f"{name}_render_log.txt").write_text(
        "Exit code: "+str(run.returncode)+"\n"+run.stderr[-24000:],
        encoding="utf-8")
    if run.returncode!=0:
        raise RuntimeError(f"Render {name} failed: {run.stderr[-2400:]}")
    p=probe(output)
    # Ensure original source provenance and current output checksum.
    manifest={
      "pipeline":"CASA_VIDEO_LAB_V2","story":name,"status":"RENDERED_LOCAL_PENDING_CONTENT_REVIEW",
      "title":story['title'],"output":output.name,"source_type":"ORIGINAL_RECORDINGS",
      "source_segments":[{"source":SOURCES[k].name,"in_seconds":start,"duration_seconds":dur,
                        "composition":mode,"center_x_normalized":cen} for k,start,dur,mode,cen in segs],
      "duration_expected_seconds":duration,"output_probe":p,
      "input_sha256":{SOURCES[k].name:sha256(SOURCES[k]) for k in {seg[0] for seg in segs}},
      "output_sha256":sha256(output),"output_size_bytes":output.stat().st_size,
      "render_seconds":round(time.time()-t0,2),
      "caption":story["caption"],"hashtags":story["tags"],
      "host":"ChatGPT sandbox, NOT WIN_HOST FAMILIA","device_QA":"NOT_EXECUTED"
    }
    mfile=ROOT/f"{name}_manifest.json";mfile.write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8")
    print(f"OK {name} -> {output.name}: {p['duration']:.2f}sec, {output.stat().st_size/1e6:.2f} MB, {manifest['render_seconds']} sec")
    return manifest
if __name__=="__main__":
    names=sys.argv[1:] or ["all"]
    if "all" in names:names=list(STORIES)
    for name in names:
        if name not in STORIES:raise SystemExit("Unknown story: "+name)
        build(name)