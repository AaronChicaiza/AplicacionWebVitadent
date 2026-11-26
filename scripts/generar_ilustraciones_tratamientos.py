"""Genera ilustraciones SVG originales y esquemáticas para el catálogo público."""

from pathlib import Path
import sys
from html import escape

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from web.datos_demo import GRUPOS_TRATAMIENTOS


DESTINO = Path(__file__).resolve().parents[1] / "web/static/web/img/procedimientos"
AZUL = "#087f89"
CIAN = "#00b9c9"
LIMA = "#c8e900"
TINTA = "#133b40"


def linea(d, color=AZUL, grosor=7, extra=""):
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{grosor}" stroke-linecap="round" stroke-linejoin="round" {extra}/>'


def circulo(x, y, radio, color=CIAN, extra=""):
    return f'<circle cx="{x}" cy="{y}" r="{radio}" fill="{color}" {extra}/>'


def diente(x=320, y=188, escala=1, relleno="#ffffff", borde=TINTA):
    contorno = 'M-69 -61 C-88 -80 -98 -124 -76 -144 C-53 -164 -27 -151 0 -148 C27 -151 53 -164 76 -144 C98 -124 88 -80 69 -61 C57 -40 53 -4 43 69 C38 105 26 124 15 119 C3 114 7 62 0 40 C-7 62 -3 114 -15 119 C-26 124 -38 105 -43 69 C-53 -4 -57 -40 -69 -61 Z'
    return f'''<g transform="translate({x} {y}) scale({escala})">
      <path d="{contorno}" fill="{relleno}" stroke="{borde}" stroke-width="6" stroke-linejoin="round"/>
      <path d="M-67 -64 Q-87 -117 -68 -133 Q-46 -151 -13 -137 Q0 -130 13 -137 Q46 -151 68 -133 Q87 -117 67 -64 Q35 -81 0 -76 Q-35 -81 -67 -64 Z" fill="#dff5f2" opacity=".85"/>
      <path d="M-31 -44 Q0 -70 31 -44 Q27 -17 14 9 Q5 29 0 50 Q-5 29 -14 9 Q-27 -17 -31 -44 Z" fill="#e7b3a5" stroke="#b97870" stroke-width="3"/>
      <path d="M-18 10 Q-24 53 -25 86 M18 10 Q24 53 25 86" fill="none" stroke="#b97870" stroke-width="4" stroke-linecap="round"/>
      <path d="M-58 -111 Q-47 -124 -31 -121" fill="none" stroke="#ffffff" stroke-width="6" stroke-linecap="round"/>
    </g>'''


def arco_dientes(n=7, y=210, pequeños=False):
    escala = .35 if pequeños else .46
    paso = 60 if pequeños else 71
    inicio = 320 - (n - 1) * paso / 2
    encia = f'<path d="M{inicio-35:.0f} {y-12} Q320 {y-60} {inicio+(n-1)*paso+35:.0f} {y-12} L{inicio+(n-1)*paso+35:.0f} {y+25} Q320 {y-5} {inicio-35:.0f} {y+25} Z" fill="#f4c8bc" opacity=".85"/>'
    return encia + "".join(diente(round(inicio + i * paso), y + int(abs(i - (n - 1) / 2) * 4), escala) for i in range(n))


def corona(x, y, escala=1):
    return f'''<g transform="translate({x} {y}) scale({escala})">
      <path d="M-46 40 Q-58 -4 -49 -36 Q-39 -55 -15 -52 Q0 -45 15 -52 Q39 -55 49 -36 Q58 -4 46 40 Q0 49 -46 40 Z" fill="#ffffff" stroke="{TINTA}" stroke-width="5" stroke-linejoin="round"/>
      <path d="M-38 -28 Q-23 -43 -6 -37" fill="none" stroke="#d8f2ef" stroke-width="6" stroke-linecap="round"/>
    </g>'''


def hilera_coronas(n, y=164, separacion=57):
    inicio = 320 - (n - 1) * separacion / 2
    return "".join(corona(round(inicio + i * separacion), y + int(abs(i - (n - 1) / 2) * 3), .65) for i in range(n))


def rostro_frontal():
    return '''<g stroke-linecap="round" stroke-linejoin="round">
      <path d="M205 138 Q190 57 320 54 Q450 57 435 138 L426 227 Q410 304 320 315 Q230 304 214 227 Z" fill="#f6d3bb" stroke="#18555b" stroke-width="6"/>
      <path d="M203 148 Q178 91 221 60 Q276 18 343 37 Q421 24 444 93 L433 147 Q415 106 390 81 Q333 103 270 78 Q228 108 203 148 Z" fill="#314d50"/>
      <path d="M213 174 Q183 152 190 194 Q197 220 218 221 M427 174 Q457 152 450 194 Q443 220 422 221" fill="#f6d3bb" stroke="#18555b" stroke-width="5"/>
      <path d="M255 162 Q280 148 301 162 M339 162 Q360 148 385 162" fill="none" stroke="#314d50" stroke-width="5"/>
      <ellipse cx="279" cy="175" rx="11" ry="7" fill="#ffffff"/><ellipse cx="361" cy="175" rx="11" ry="7" fill="#ffffff"/>
      <circle cx="280" cy="175" r="5" fill="#18555b"/><circle cx="360" cy="175" r="5" fill="#18555b"/>
      <path d="M320 177 Q311 212 320 218 L335 220" fill="none" stroke="#b77e70" stroke-width="4"/>
      <path d="M274 249 Q320 282 366 249 Q345 293 320 291 Q295 293 274 249 Z" fill="#8d5961" stroke="#a26d72" stroke-width="3"/>
      <path d="M281 253 Q320 268 359 253 L351 268 Q320 276 289 268 Z" fill="#ffffff"/>
      <path d="M282 252 Q320 238 358 252" fill="none" stroke="#ae7373" stroke-width="4"/>
    </g>'''


def rostro_perfil():
    return '''<g stroke-linecap="round" stroke-linejoin="round">
      <path d="M244 94 Q319 33 387 83 Q425 109 418 164 L449 203 Q453 213 434 219 L414 225 Q427 238 408 248 Q417 260 403 274 Q383 303 332 292 L317 326 L231 326 Q248 279 235 236 Q188 168 244 94 Z" fill="#f6d3bb" stroke="#18555b" stroke-width="6"/>
      <path d="M239 134 Q211 72 292 54 Q365 35 410 98 Q374 86 350 74 Q299 106 261 103 Z" fill="#314d50"/>
      <ellipse cx="251" cy="195" rx="22" ry="30" fill="#f1c5ae" stroke="#b77e70" stroke-width="4"/>
      <path d="M360 164 Q383 151 400 166" fill="none" stroke="#314d50" stroke-width="5"/>
      <ellipse cx="382" cy="172" rx="8" ry="6" fill="#ffffff"/><circle cx="384" cy="172" r="4" fill="#18555b"/>
      <path d="M397 233 Q416 226 429 233 M395 246 Q410 253 422 245" fill="none" stroke="#a9686a" stroke-width="4"/>
      <path d="M325 273 Q352 292 386 275" fill="none" stroke="#b77e70" stroke-width="3"/>
    </g>'''


def boca_abierta():
    return '''<path d="M171 179 Q320 105 469 179 Q449 291 320 312 Q191 291 171 179 Z" fill="#913f59" stroke="#18555b" stroke-width="7"/>
      <path d="M182 180 Q320 124 458 180 Q320 230 182 180 Z" fill="#ffffff" stroke="#d9a7a1" stroke-width="4"/>
      <path d="M233 250 Q320 201 407 250 Q320 298 233 250 Z" fill="#e7a0a2" stroke="#bd7383" stroke-width="4"/>
      <path d="M178 166 Q320 105 462 166 M178 192 Q320 328 462 192" fill="none" stroke="#eeb6a8" stroke-width="13" stroke-linecap="round"/>'''


def bracket(x, y, tipo="normal"):
    if tipo == "transparente":
        return f'<rect x="{x-17}" y="{y-17}" width="34" height="34" rx="7" fill="#c6eef0" fill-opacity=".4" stroke="{AZUL}" stroke-width="4"/>'
    base = f'<rect x="{x-16}" y="{y-16}" width="32" height="32" rx="5" fill="{AZUL}"/>'
    if tipo == "autoligado":
        return base + f'<rect x="{x-9}" y="{y-8}" width="18" height="16" rx="2" fill="{LIMA}"/>'
    return base + linea(f"M{x-10} {y} H{x+10}", "#ffffff", 3)


def rayos(indice):
    pantalla = '<rect x="115" y="53" width="410" height="285" rx="20" fill="#173840"/>'
    brillo = '<rect x="129" y="67" width="382" height="257" rx="12" fill="#244d55"/>'
    if indice == 1:  # panorámica: ambas arcadas completas
        dibujo = linea("M161 174 Q320 58 479 174 M161 204 Q320 317 479 204", "#b9e8e8", 8)
        dibujo += "".join(f'<g transform="translate({x} 142) scale(.26) rotate(180)">{diente(0,0,1,"#cce6e2","#e5fff4")}</g>' for x in range(190, 471, 40))
        dibujo += "".join(diente(x, 227, .26, "#cce6e2", "#e5fff4") for x in range(190, 471, 40))
        dibujo += linea("M320 92 V288", LIMA, 3, 'stroke-dasharray="5 8"')
    elif indice == 2:  # periapical: pieza y raíz
        dibujo = diente(320, 180, .84, "#cce6e2", "#e5fff4") + linea("M249 225 Q320 190 391 225", LIMA, 5)
        dibujo += circulo(320, 270, 14, "none", f'stroke="{LIMA}" stroke-width="5"')
    elif indice == 3:  # lateral de cráneo: perfil
        dibujo = '<g transform="translate(0 1)" opacity=".86">' + rostro_perfil() + '</g>'
        dibujo += linea("M279 227 Q340 210 412 240", LIMA, 6) + linea("M207 268 H425", "#b9e8e8", 3, 'stroke-dasharray="7 7"')
    else:  # carpal: mano y muñeca
        dibujo = linea("M260 301 L256 227 L224 164 Q219 150 232 145 Q241 143 250 157 L280 204 L270 105 Q269 90 281 89 Q293 90 294 105 L304 187 L307 80 Q308 68 320 67 Q333 69 333 84 L334 185 L351 99 Q355 87 367 90 Q378 95 373 109 L360 198 L384 143 Q393 131 405 138 Q414 146 406 159 L366 245 L350 301 Z", "#d2f3ec", 9)
        dibujo += "".join(linea(f"M{x} {y} v25", LIMA, 3) for x, y in ((282, 118), (320, 100), (359, 122)))
        dibujo += "".join(circulo(x, y, 6, LIMA) for x, y in ((282, 160), (320, 143), (359, 159), (289, 230), (331, 227)))
    return pantalla + brillo + dibujo


def general(indice, infantil=False):
    art = diente(316, 181, .84 if infantil else 1)
    if indice == 1:
        art += '<circle cx="440" cy="103" r="35" fill="#b8e6e3" stroke="#087f89" stroke-width="7"/>'
        art += linea("M417 128 L380 172", AZUL, 9) + linea("M310 163 Q320 146 336 160", LIMA, 5)
    elif indice == 2:
        art += linea("M448 61 Q423 111 391 137 L366 148", AZUL, 13) + linea("M448 61 l32 -13", TINTA, 8)
        art += linea("M255 146 Q320 140 386 146", LIMA, 9)
        art += circulo(243, 136, 7, LIMA) + circulo(405, 151, 6, LIMA)
    elif indice == 3:
        art += linea("M249 75 Q320 45 391 75 M260 76 L270 146 M380 76 L370 146", AZUL, 11)
        art += linea("M320 318 V283 M320 318 l-12 -15 M320 318 l12 -15", LIMA, 6)
    elif indice == 4:
        art += linea("M258 105 Q320 137 382 105", LIMA, 20)
        art += linea("M272 125 Q320 145 368 125", AZUL, 3)
        art += linea("M460 81 L381 106", AZUL, 8) + circulo(462, 80, 10, "#c8e900")
    elif indice == 5:
        art += '<path d="M289 61 Q320 78 351 61 L346 100 Q320 119 294 100 Z" fill="#a7deda" stroke="#087f89" stroke-width="6"/>'
    elif indice == 6:
        art += linea("M245 115 Q320 82 395 115", AZUL, 9) + circulo(323, 145, 10, LIMA)
    return art + (f'<path d="M147 90 Q163 72 179 90" fill="none" stroke="{LIMA}" stroke-width="7" stroke-linecap="round"/>' if infantil else "")


def ortodoncia(indice):
    art = arco_dientes(6, 206)
    if indice == 1:
        return art + linea("M163 115 Q320 80 477 115 M166 301 Q320 340 474 301", AZUL, 8) + linea("M320 97 V301", LIMA, 4, 'stroke-dasharray="12 10"')
    if indice in (2, 3, 4, 7):
        tipo = "autoligado" if indice == 3 else "normal"
        art += linea("M143 165 Q320 181 498 165", LIMA if indice == 4 else AZUL, 5)
        posiciones = (143, 214, 285, 356, 427, 498)
        art += "".join(bracket(x, 168 if indice != 4 else 193, tipo) for x in posiciones)
        if indice == 4:
            art += linea("M169 205 Q320 233 471 205", AZUL, 4, 'stroke-dasharray="6 8"')
        if indice == 7:
            art += '<rect x="125" y="146" width="36" height="45" rx="6" fill="none" stroke="#c8e900" stroke-width="5"/><rect x="480" y="146" width="36" height="45" rx="6" fill="none" stroke="#c8e900" stroke-width="5"/>'
    elif indice == 5:
        art += '<path d="M130 124 Q320 91 510 124 L497 212 Q320 251 143 212 Z" fill="#b3e6e6" fill-opacity=".48" stroke="#087f89" stroke-width="6"/>'
    elif indice == 6:
        art += linea("M178 285 Q320 343 462 285", AZUL, 12) + linea("M185 287 L145 238 M455 287 L495 238", LIMA, 7)
    return art


def cirugia(indice):
    if indice == 1:
        art = linea("M143 253 Q320 318 497 253", AZUL, 13) + linea("M150 262 Q320 327 490 262", "#f4c8bc", 12)
        art += diente(245, 172, .48) + diente(320, 171, .48)
        art += '<g transform="translate(404 218) rotate(-43)">' + diente(0, 0, .51) + '</g>'
        art += circulo(400, 219, 58, "none", f'stroke="{LIMA}" stroke-width="6" stroke-dasharray="8 7"')
        return art
    if indice == 2:
        return boca_abierta() + linea("M320 210 V270", LIMA, 10) + circulo(320, 228, 16, "none", f'stroke="{AZUL}" stroke-width="5"')
    if indice == 3:
        return rostro_frontal() + circulo(232, 224, 28, "#c8e900", 'fill-opacity=".42"') + circulo(408, 224, 28, "#c8e900", 'fill-opacity=".42"') + linea("M168 224 H195 M472 224 H445", AZUL, 5)
    if indice == 4:
        return rostro_perfil() + '<path d="M331 284 Q374 305 409 267 Q397 304 352 319 Z" fill="#c8e900" fill-opacity=".65" stroke="#087f89" stroke-width="4"/>' + linea("M404 313 L445 286", AZUL, 5)
    return rostro_perfil() + linea("M278 257 Q338 245 411 271", LIMA, 8) + circulo(351, 252, 29, "none", f'stroke="{AZUL}" stroke-width="5"') + linea("M198 292 L257 268", AZUL, 5)


def rehabilitacion(indice):
    if indice == 1:
        return diente(320, 181, .96) + "".join(linea(f"M{x} {y-14} v28 M{x-14} {y} h28", LIMA, 5) for x, y in ((184, 115), (451, 124), (440, 275)))
    if indice == 2:
        return hilera_coronas(7, 177) + linea("M110 243 Q320 294 530 243", AZUL, 7)
    if indice == 3:
        return hilera_coronas(7, 175) + '<path d="M105 206 Q320 255 535 206 L519 263 Q320 325 121 263 Z" fill="#e7a9a6" stroke="#087f89" stroke-width="6"/>'
    if indice == 4:
        return hilera_coronas(5, 173) + '<path d="M170 209 Q320 256 470 209 L458 268 Q320 309 182 268 Z" fill="#e7a9a6" stroke="#087f89" stroke-width="6"/>' + linea("M180 225 q-20 -25 -30 0 M460 225 q20 -25 30 0", AZUL, 6)
    return hilera_coronas(3, 166) + linea("M215 213 Q320 240 425 213", AZUL, 10) + linea("M230 208 V271 M410 208 V271", LIMA, 6)


def endodoncia(indice):
    art = diente(320, 181, 1)
    if indice == 1:
        art += linea("M320 145 V261", LIMA, 8) + circulo(320, 265, 16, "#e67e70") + linea("M437 159 l-31 39", AZUL, 6)
    elif indice == 2:
        art += linea("M320 145 V259", AZUL, 6) + circulo(320, 280, 28, "none", f'stroke="{LIMA}" stroke-width="8"') + linea("M287 297 l66 -31", AZUL, 6)
    else:
        art += '<rect x="307" y="112" width="26" height="145" rx="7" fill="#087f89"/>' + linea("M320 87 V112 M294 145 H346", LIMA, 6)
    return art


def implante(indice):
    tornillo = '<path d="M296 184 H344 L338 278 L320 302 L302 278 Z" fill="#9bd7d6" stroke="#087f89" stroke-width="7"/>'
    tornillo += "".join(linea(f"M301 {y} L339 {y+12}", AZUL, 5) for y in (201, 223, 245, 267))
    base = '<path d="M146 248 Q320 223 494 248 L494 302 Q320 276 146 302 Z" fill="#f1c4b4" stroke="#087f89" stroke-width="6"/>'
    if indice == 1:
        return base + corona(320, 120, 1.13) + linea("M320 166 V184", AZUL, 7) + tornillo
    if indice == 2:
        return base + hilera_coronas(4, 145, 75) + linea("M190 195 H450", AZUL, 7) + tornillo + '<g transform="translate(126 0)">' + tornillo + '</g>'
    if indice == 3:
        return base + tornillo + linea("M195 305 Q320 238 445 305", AZUL, 7) + "".join(circulo(x, y, 7, LIMA) for x, y in ((220, 277), (260, 261), (380, 261), (420, 277)))
    return base + tornillo + '<path d="M196 270 Q245 225 295 264 L295 311 Q244 269 196 313 Z" fill="#cde8ae" stroke="#087f89" stroke-width="7"/>' + linea("M215 276 L275 289", AZUL, 5)


def ilustracion(area, indice):
    if area == "rayos-x":
        return rayos(indice)
    if area == "odontologia-general":
        return general(indice)
    if area == "ortodoncia":
        return ortodoncia(indice)
    if area == "cirugia-maxilofacial":
        return cirugia(indice)
    if area == "rehabilitacion-oral":
        return rehabilitacion(indice)
    if area == "odontopediatria":
        return {
            1: ortodoncia(6),
            2: endodoncia(1),
            3: ortodoncia(7),
            4: general(2, infantil=True),
            5: general(5, infantil=True),
            6: general(3, infantil=True),
        }[indice]
    if area == "endodoncia":
        return endodoncia(indice)
    return implante(indice)


ETIQUETAS = {
    "rayos-x": [
        ("Arcadas completas", "Vista panorámica"),
        ("Pieza y raíz", "Imagen localizada"),
        ("Perfil del cráneo", "Relación maxilar"),
        ("Mano y muñeca", "Maduración ósea"),
    ],
    "odontologia-general": [
        ("Exploración clínica", "Dientes y encías"),
        ("Instrumento de limpieza", "Placa y cálculo"),
        ("Pieza a retirar", "Extracción indicada"),
        ("Superficie masticatoria", "Capa protectora"),
    ],
    "ortodoncia": [
        ("Maxilares y mordida", "Plan conjunto"),
        ("Brackets y arco", "Alineación gradual"),
        ("Clip integrado", "Arco sujetado"),
        ("Cara interna", "Aparato lingual"),
        ("Férula removible", "Movimiento planificado"),
        ("Aparato ortopédico", "Guía del crecimiento"),
        ("Cuatro incisivos", "Dos molares"),
    ],
    "cirugia-maxilofacial": [
        ("Tercer molar", "Posición inclinada"),
        ("Frenillo oral", "Zona de intervención"),
        ("Anatomía de mejillas", "Grasa bucal"),
        ("Perfil facial", "Zona submentoniana"),
        ("Maxilar", "Plan quirúrgico"),
    ],
    "rehabilitacion-oral": [
        ("Diente natural", "Agente blanqueador"),
        ("Arco dental", "Plan estético"),
        ("Arcada completa", "Prótesis total"),
        ("Dientes ausentes", "Prótesis removible"),
        ("Piezas de apoyo", "Restauración fija"),
    ],
    "odontopediatria": [
        ("Maxilares en desarrollo", "Aparato indicado"),
        ("Diente infantil", "Tratamiento interno"),
        ("Dentición mixta", "Ortodoncia temprana"),
        ("Higiene infantil", "Limpieza clínica"),
        ("Caries", "Restauración dental"),
        ("Diente infantil", "Extracción indicada"),
    ],
    "endodoncia": [
        ("Pulpa dental", "Causa del dolor"),
        ("Extremo de la raíz", "Cirugía apical"),
        ("Raíz tratada", "Soporte restaurador"),
    ],
    "implantologia": [
        ("Implante y corona", "Diente unitario"),
        ("Varios implantes", "Prótesis de apoyo"),
        ("Hueso de soporte", "Regeneración"),
        ("Zona receptora", "Tejido injertado"),
    ],
}


def svg(area, indice, nombre):
    fondo = "#eff8f5" if indice % 2 else "#edf6f6"
    arte = ilustracion(area, indice)
    etiqueta_1, etiqueta_2 = ETIQUETAS[area][indice - 1]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 400" role="img">
<title>{escape(nombre)}</title>
<rect width="640" height="400" fill="{fondo}"/>
<rect x="42" y="28" width="556" height="344" rx="25" fill="#ffffff" stroke="#cde1dd" stroke-width="2"/>
{arte}
<rect x="43" y="329" width="554" height="42" rx="0" fill="#e3f4ef"/>
<path d="M43 329 H597" stroke="#b6d8d3" stroke-width="2"/>
<circle cx="70" cy="350" r="6" fill="{AZUL}"/>
<text x="84" y="356" font-family="Arial, sans-serif" font-size="17" font-weight="700" fill="{TINTA}">{escape(etiqueta_1)}</text>
<circle cx="362" cy="350" r="6" fill="{LIMA}"/>
<text x="376" y="356" font-family="Arial, sans-serif" font-size="17" font-weight="700" fill="{TINTA}">{escape(etiqueta_2)}</text>
</svg>'''


def main():
    DESTINO.mkdir(parents=True, exist_ok=True)
    for grupo in GRUPOS_TRATAMIENTOS:
        for indice, nombre in enumerate(grupo["procedimientos"], start=1):
            ruta = DESTINO / f"{grupo['id']}-{indice:02}.svg"
            ruta.write_text(svg(grupo["id"], indice, nombre), encoding="utf-8")
    print(f"Generadas {sum(len(grupo['procedimientos']) for grupo in GRUPOS_TRATAMIENTOS)} ilustraciones en {DESTINO}")


if __name__ == "__main__":
    main()
