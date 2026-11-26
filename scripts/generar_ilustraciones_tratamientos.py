"""Genera ilustraciones SVG originales y esquemáticas para el catálogo público."""

from pathlib import Path
import sys

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
    return f'<g transform="translate({x} {y}) scale({escala})"><path d="M-69 -61 C-88 -80 -98 -124 -76 -144 C-53 -164 -27 -151 0 -148 C27 -151 53 -164 76 -144 C98 -124 88 -80 69 -61 C57 -40 53 -4 43 69 C38 105 26 124 15 119 C3 114 7 62 0 40 C-7 62 -3 114 -15 119 C-26 124 -38 105 -43 69 C-53 -4 -57 -40 -69 -61 Z" fill="{relleno}" stroke="{borde}" stroke-width="7" stroke-linejoin="round"/></g>'


def arco_dientes(n=7, y=210, pequeños=False):
    escala = .35 if pequeños else .46
    paso = 60 if pequeños else 71
    inicio = 320 - (n - 1) * paso / 2
    return "".join(diente(round(inicio + i * paso), y + int(abs(i - (n - 1) / 2) * 4), escala) for i in range(n))


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
        dibujo = linea("M170 169 Q320 45 470 169", "#b9e8e8", 11) + linea("M169 192 Q320 312 471 192", "#b9e8e8", 11)
        dibujo += "".join(linea(f"M{x} {y} l{-9 if x < 320 else 9} {25 if y < 190 else -25}", "#d4f7ef", 6) for y in (143, 220) for x in range(204, 445, 40))
    elif indice == 2:  # periapical: pieza y raíz
        dibujo = diente(320, 176, 1.08, "#bad9d6", "#e5fff4") + linea("M320 117 V272", LIMA, 5) + circulo(320, 276, 12, "none", f'stroke="{LIMA}" stroke-width="4"')
    elif indice == 3:  # lateral de cráneo: perfil
        dibujo = linea("M253 95 Q392 64 432 166 Q458 207 424 222 L394 222 L388 250 Q373 299 314 290 Q247 270 231 203 Q215 139 253 95 Z", "#d2f3ec", 9)
        dibujo += linea("M366 161 Q384 151 404 163 M392 190 L434 203 L392 211 M274 232 Q340 209 389 234", LIMA, 5)
    else:  # carpal: mano y muñeca
        dibujo = linea("M260 301 L256 227 L224 164 Q219 150 232 145 Q241 143 250 157 L280 204 L270 105 Q269 90 281 89 Q293 90 294 105 L304 187 L307 80 Q308 68 320 67 Q333 69 333 84 L334 185 L351 99 Q355 87 367 90 Q378 95 373 109 L360 198 L384 143 Q393 131 405 138 Q414 146 406 159 L366 245 L350 301 Z", "#d2f3ec", 9)
        dibujo += "".join(circulo(x, y, 5, LIMA) for x, y in ((282, 160), (320, 143), (359, 159), (289, 230), (331, 227)))
    return pantalla + brillo + dibujo


def general(indice, infantil=False):
    art = diente(316, 181, .84 if infantil else 1)
    if indice == 1:
        art += linea("M396 128 L443 83 M411 125 L452 125 M391 109 L391 70", LIMA, 7)
    elif indice == 2:
        art += linea("M451 70 Q429 140 392 181 L353 193", AZUL, 12) + linea("M450 70 l32 -17", TINTA, 9)
        art += circulo(245, 133, 8, LIMA) + circulo(407, 244, 6, LIMA)
    elif indice == 3:
        art += linea("M260 89 L270 152 M380 89 L370 152 M253 89 Q320 54 387 89", AZUL, 12)
        art += linea("M320 311 v-28", LIMA, 7)
    elif indice == 4:
        art += linea("M258 104 Q320 136 382 104", LIMA, 18) + linea("M269 113 Q319 142 371 113", AZUL, 4)
    elif indice == 5:
        art += '<rect x="292" y="121" width="56" height="130" rx="17" fill="#94d7d6" stroke="#087f89" stroke-width="7"/>'
    elif indice == 6:
        art += linea("M245 115 Q320 82 395 115", AZUL, 9) + circulo(323, 145, 10, LIMA)
    return art + (circulo(158, 90, 18, LIMA) if infantil else "")


def ortodoncia(indice):
    art = arco_dientes(6, 206)
    if indice == 1:
        return art + linea("M163 115 Q320 80 477 115 M166 301 Q320 340 474 301", AZUL, 8) + linea("M320 97 V301", LIMA, 4, 'stroke-dasharray="12 10"')
    if indice in (2, 3, 4, 7):
        tipo = "autoligado" if indice == 3 else "normal"
        art += linea("M154 220 Q320 244 486 220", LIMA if indice == 4 else AZUL, 5)
        posiciones = (214, 285, 356, 427) if indice == 7 else (143, 214, 285, 356, 427, 498)
        art += "".join(bracket(x, 221 if indice != 4 else 245, tipo) for x in posiciones)
        if indice == 4:
            art += linea("M169 273 Q320 304 471 273", AZUL, 4, 'stroke-dasharray="6 8"')
    elif indice == 5:
        art += '<path d="M130 180 Q320 137 510 180 L497 265 Q320 310 143 265 Z" fill="#b3e6e6" fill-opacity=".38" stroke="#087f89" stroke-width="7"/>'
    elif indice == 6:
        art += linea("M178 285 Q320 343 462 285", AZUL, 12) + linea("M185 287 L145 238 M455 287 L495 238", LIMA, 7)
    return art


def cirugia(indice):
    if indice == 1:
        return diente(305, 180, .91) + linea("M421 90 Q449 160 402 223", AZUL, 11) + linea("M415 89 l28 -13", TINTA, 7)
    if indice == 2:
        return linea("M175 215 Q320 282 465 215 M320 153 V227", AZUL, 10) + linea("M287 176 L351 213", LIMA, 9) + linea("M335 178 L307 210", LIMA, 9)
    if indice == 3:
        return linea("M228 88 Q169 178 239 278 Q303 340 409 280 Q467 193 415 98 M301 200 Q320 222 341 200", AZUL, 9) + circulo(243, 211, 31, "#afe2df") + circulo(397, 211, 31, "#afe2df")
    if indice == 4:
        return linea("M253 74 Q344 88 380 165 Q421 217 374 282 L341 303 M266 281 Q310 310 341 303", AZUL, 10) + linea("M305 282 Q351 272 384 238", LIMA, 9)
    return diente(323, 179, .76) + linea("M165 268 Q320 323 475 268", AZUL, 11) + linea("M320 107 L320 58 M320 58 L308 74 M320 58 L332 74", LIMA, 6)


def rehabilitacion(indice):
    if indice == 1:
        return diente(320, 181, .96) + "".join(linea(f"M{x} {y-14} v28 M{x-14} {y} h28", LIMA, 5) for x, y in ((184, 115), (451, 124), (440, 275)))
    if indice == 2:
        return arco_dientes(7, 211) + linea("M119 284 Q320 359 521 284", AZUL, 9)
    if indice == 3:
        return arco_dientes(7, 194) + linea("M112 292 Q320 359 528 292 Q320 313 112 292", AZUL, 9)
    if indice == 4:
        return arco_dientes(5, 189) + linea("M175 297 Q320 338 465 297", AZUL, 11) + linea("M180 297 v-44 M460 297 v-44", LIMA, 6)
    return arco_dientes(3, 190) + linea("M180 293 Q320 333 460 293", AZUL, 12) + linea("M243 232 V294 M397 232 V294", LIMA, 6)


def endodoncia(indice):
    art = diente(320, 181, 1)
    if indice == 1:
        art += linea("M319 102 V264", AZUL, 7) + circulo(320, 265, 14, LIMA) + linea("M437 159 l-31 39", AZUL, 6)
    elif indice == 2:
        art += linea("M320 103 V263", AZUL, 6) + circulo(320, 280, 28, "none", f'stroke="{LIMA}" stroke-width="8"') + linea("M287 297 l66 -31", AZUL, 6)
    else:
        art += '<rect x="305" y="119" width="30" height="137" rx="8" fill="#087f89"/>' + linea("M320 98 V120 M296 150 H344", LIMA, 6)
    return art


def implante(indice):
    tornillo = '<path d="M296 184 H344 L338 278 L320 302 L302 278 Z" fill="#9bd7d6" stroke="#087f89" stroke-width="7"/>'
    tornillo += "".join(linea(f"M301 {y} L339 {y+12}", AZUL, 5) for y in (201, 223, 245, 267))
    if indice == 1:
        return diente(320, 94, .43) + tornillo
    if indice == 2:
        return arco_dientes(4, 156) + tornillo + '<g transform="translate(126 0)">' + tornillo + '</g>'
    if indice == 3:
        return tornillo + linea("M195 305 Q320 238 445 305", AZUL, 9) + "".join(circulo(x, y, 8, LIMA) for x, y in ((220, 277), (260, 261), (380, 261), (420, 277)))
    return tornillo + '<path d="M196 270 Q245 225 295 264 L295 311 Q244 269 196 313 Z" fill="#cde8ae" stroke="#087f89" stroke-width="7"/>' + linea("M215 276 L275 289", AZUL, 5)


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


def svg(area, indice):
    fondo = "#eff8f5" if indice % 2 else "#edf6f6"
    arte = ilustracion(area, indice)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 400" role="img">
<rect width="640" height="400" fill="{fondo}"/>
<circle cx="535" cy="58" r="115" fill="#dff0e8"/>
<circle cx="85" cy="365" r="105" fill="#e4f3ed"/>
<rect x="42" y="28" width="556" height="344" rx="25" fill="#ffffff" fill-opacity=".68" stroke="#cde1dd" stroke-width="2"/>
{arte}
<path d="M70 343 H570" stroke="#a7d4ce" stroke-width="2"/>
</svg>'''


def main():
    DESTINO.mkdir(parents=True, exist_ok=True)
    for grupo in GRUPOS_TRATAMIENTOS:
        for indice, _ in enumerate(grupo["procedimientos"], start=1):
            ruta = DESTINO / f"{grupo['id']}-{indice:02}.svg"
            ruta.write_text(svg(grupo["id"], indice), encoding="utf-8")
    print(f"Generadas {sum(len(grupo['procedimientos']) for grupo in GRUPOS_TRATAMIENTOS)} ilustraciones en {DESTINO}")


if __name__ == "__main__":
    main()
