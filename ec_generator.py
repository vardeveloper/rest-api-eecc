from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib import pdfencrypt
from reportlab.lib.utils import ImageReader

import os
from cStringIO import StringIO
import textwrap


class ECGenerator(object):

    def __init__(self, ec_type, user_type, font_color='#717175'):
        base_path = os.path.dirname(__file__)
        self.assets_path = os.path.join(base_path, 'assets')

        self._front_image_inst = Image.open(os.path.join(
            self.assets_path,
            ec_type + '_' + user_type + '_tira.png'
        )).convert('RGBA')
        self._front_draw_inst = ImageDraw.Draw(self._front_image_inst)

        self._back_image_inst = Image.open(os.path.join(
            self.assets_path,
            ec_type + '_' + user_type + '_retira.png'
        )).convert('RGBA')
        self._back_draw_inst = ImageDraw.Draw(self._back_image_inst)

        self._ec_type = ec_type
        self._user_type = user_type
        self._font_color = font_color
        self._fonts = {}

    def _get_font(self, font, size):
        font = font.lower()
        font_name = os.path.splitext(font)[0]
        if self._fonts.get(font_name, None) is None:
            self._fonts.update({
                font_name: {
                    size: ImageFont.truetype(
                        os.path.join(self.assets_path, font),
                        size
                    )
                }
            })
        elif self._fonts.get(font_name).get(size, None) is None:
            self._fonts.get(font_name).update({
                size: ImageFont.truetype(
                    os.path.join(self.assets_path, font),
                    size
                )
            })
        return self._fonts.get(font_name).get(size)

    def align_right(self, x, value, font, size):
        _font = self._get_font(font, size)
        return x - _font.getsize(value)[0]

    def _draw_text(self, draw_inst, position, value, color, font, size,
                   center=True):
        _font = self._get_font(font, size)
        if center:
            position = (
                position[0] - (_font.getsize(value)[0] / 2),
                position[1]
            )
        draw_inst.text(position, value, fill=color, font=_font)

    def export(self, password_protect=False, doc_number=None):
        if password_protect and not doc_number:
            raise Exception(
                'doc_number is required if file is password protected'
            )

        _pagesize = (595, 842)
        res = StringIO()
        if password_protect:
            _enc = pdfencrypt.StandardEncryption(
                doc_number,
                canPrint=True,
                canCopy=False
            )
            output = canvas.Canvas(res, pagesize=_pagesize, encrypt=_enc)
        else:
            output = canvas.Canvas(res, pagesize=_pagesize)

        output.drawImage(
            ImageReader(self._front_image_inst.copy()),
            0,
            0,
            *_pagesize
        )
        output.showPage()
        output.drawImage(
            ImageReader(self._back_image_inst.copy()),
            0,
            0,
            *_pagesize
        )
        output.save()
        return res.getvalue()

    def _set_header(self, position, name, address, cuspp, doc_number,
                    scheme, last_input_date):
        # name
        self._draw_text(
            self._front_draw_inst,
            (position[0] + 160, position[1] + 16),
            name,
            self._font_color,
            'DINPro-Regular.otf',
            30,
            False
        )
        # address
        for index, line in enumerate(address):
            self._draw_text(
                self._front_draw_inst,
                (position[0] + 19, position[1] + 125 + (index * 25)),
                line,
                self._font_color,
                'DINPro-Regular.otf',
                22,
                False
            )
        # cuspp
        self._draw_text(
            self._front_draw_inst,
            (position[0] + 19, position[1] + 290),
            cuspp,
            self._font_color,
            'DINPro-Regular.otf',
            22,
            False
        )
        # doc_type doc_number
        self._draw_text(
            self._front_draw_inst,
            (position[0] + 320, position[1] + 290),
            doc_number,
            self._font_color,
            'DINPro-Regular.otf',
            22
        )
        # scheme
        scheme_wrap = textwrap.wrap(scheme, 20)
        if len(scheme_wrap) > 1:
            for index, line in enumerate(scheme_wrap):
                self._draw_text(
                    self._front_draw_inst,
                    (position[0] + 570, position[1] + 280 + (index * 25)),
                    line,
                    self._font_color,
                    'DINPro-Regular.otf',
                    22
                )

        # last input date
        self._draw_text(
            self._front_draw_inst,
            (position[0] + 775, position[1] + 290),
            last_input_date,
            self._font_color,
            'DINPro-Regular.otf',
            22
        )

    def _set_resume(self, position, current_date, total, input_info):
        # current_date
        self._draw_text(
            self._front_draw_inst,
            (position[0] + 35, position[1] + 75),
            current_date,
            self._font_color,
            'DINPro-Medium.otf',
            25,
            False
        )
        # total
        self._draw_text(
            self._front_draw_inst,
            (position[0] + 35, position[1] + 150),
            total,
            self._font_color,
            'DINPro-Medium.otf',
            40,
            False
        )
        # input_info
        self._draw_text(
            self._front_draw_inst,
            (position[0] + 35, position[1] + 268),
            input_info,
            self._font_color,
            'DINPro-Regular.otf',
            22,
            False
        )

    def _set_input_table(self, position, data, vspace):
        _coords = {
            '3': (0, 450, 900),
            '5': (0, 240, 470, 710, 945),
            '6': (0, 205, 390, 600, 790, 985)
        }
        coords = _coords.get(str(len(data[0])))

        for index, item in enumerate(data):
            for cindex, citem in enumerate(item):
                self._draw_text(
                    self._front_draw_inst,
                    (position[0] + coords[cindex],
                     position[1] + (index * vspace)),
                    citem,
                    self._font_color,
                    'DINPro-Regular.otf',
                    22
                )

    def _set_movements(self, position, data):
        for index, item in enumerate(data):
            self._draw_text(
                self._front_draw_inst,
                (position[0], position[1] + (index * 38)),
                item[0],
                self._font_color,
                'DINPro-Regular.otf',
                22
            )
            self._draw_text(
                self._front_draw_inst,
                (position[0] + 165, position[1] + (index * 38)),
                item[1],
                self._font_color,
                'DINPro-Regular.otf',
                22
            )
            self._draw_text(
                self._front_draw_inst,
                (position[0] + 385, position[1] + (index * 38)),
                item[2],
                self._font_color,
                'DINPro-Regular.otf',
                22
            )
            self._draw_text(
                self._front_draw_inst,
                (position[0] + 650, position[1] + (index * 38)),
                item[3],
                self._font_color,
                'DINPro-Regular.otf',
                22
            )
            self._draw_text(
                self._front_draw_inst,
                (position[0] + 1030, position[1] + (index * 38)),
                item[4],
                self._font_color,
                'DINPro-Regular.otf',
                22
            )
            self._draw_text(
                self._front_draw_inst,
                (
                    self.align_right(
                        position[0] + 1415,
                        item[5],
                        'DINPro-Regular.otf',
                        22
                    ),
                    position[1] + (index * 38)
                ),
                item[5],
                self._font_color,
                'DINPro-Regular.otf',
                22,
                False
            )

    def _set_discount_table(self, position, insurance, commision):
        self._draw_text(
            self._front_draw_inst,
            (position[0], position[1]),
            insurance,
            self._font_color,
            'DINPro-Regular.otf',
            22
        )
        self._draw_text(
            self._front_draw_inst,
            (position[0] + 750, position[1]),
            commision,
            self._font_color,
            'DINPro-Regular.otf',
            22
        )

    def _set_resume_table(self, position, inputs, retires, rent, total):
        self._draw_text(
            self._front_draw_inst,
            (position[0], position[1]),
            inputs,
            self._font_color,
            'DINPro-Regular.otf',
            22
        )
        self._draw_text(
            self._front_draw_inst,
            (position[0] + 380, position[1]),
            retires,
            self._font_color,
            'DINPro-Regular.otf',
            22
        )
        self._draw_text(
            self._front_draw_inst,
            (position[0] + 750, position[1]),
            rent,
            self._font_color,
            'DINPro-Regular.otf',
            22
        )
        self._draw_text(
            self._front_draw_inst,
            (position[0] + 1128, position[1]),
            total,
            self._font_color,
            'DINPro-Regular.otf',
            22
        )

    def _set_notes(self, position, data):
        index = 0
        for line in data:
            for innerline in textwrap.wrap(line, 170):
                self._draw_text(
                    self._back_draw_inst,
                    (position[0], position[1] + (index * 25)),
                    innerline,
                    self._font_color,
                    'DINPro-Regular.otf',
                    18,
                    False
                )
                index += 1

    def render(self, data):
        self._set_header(
            (78, 194),
            data.get('nomCliente', ''),
            (
                data.get('desDirecc1', ''),
                data.get('desDirecc2', ''),
                data.get('desDirecc3', '')
            ),
            data.get('idNss', ''),
            data.get('numDocume', ''),
            data.get('tipoComision', ''),
            data.get('ultMesAporte', '')
        )
        self._set_resume(
            (965, 194),
            data.get('fecReporte', ''),
            data.get('saldoTotal', ''),
            data.get('fecLargaSaldoActual', '')
        )
        self._draw_text(
            self._front_draw_inst,
            (617, 602),
            '(Del %s al %s)' % (
                data.get('primerAporte', ''),
                data.get('fecFinal', '')
            ),
            self._font_color,
            'DINPro-Regular.otf',
            22,
            False
        )

        if self._ec_type == 'flujo':
            self._set_input_table(
                (510, 798),
                (
                    (
                        data.get('fondoOblInaf', ''),
                        data.get('aporteOblInaf', ''),
                        data.get('cargosOblInaf', ''),
                        data.get('rendimientoOblInaf', ''),
                        data.get('saldoOblInaf', '')
                    ),
                ),
                65
            )
            self._set_input_table(
                (488, 990),
                (
                    (
                        data.get('fondoVcf', ''),
                        data.get('aporteVcf', ''),
                        data.get('cargosVcf', ''),
                        data.get('rendimientoVcf', ''),
                        data.get('comisionVcf', ''),
                        data.get('saldoVcf', '')
                    ),
                    (
                        data.get('fondoVsf', ''),
                        data.get('aporteVsf', ''),
                        data.get('cargosVsf', ''),
                        data.get('rendimientoVsf', ''),
                        data.get('comisionVsf', ''),
                        data.get('saldoVsf', '')
                    )
                ),
                65
            )
            self._set_input_table(
                (453, 1330),
                (
                    (
                        data.get('bonoSituacion', ''),
                        data.get('bonoNominal', ''),
                        data.get('bonoActualizado', '')
                    )
                ),
                65
            )

            self._draw_text(
                self._front_draw_inst,
                (429, 1330),
                '(Del %s al %s)' % (
                    data.get('fecIniSaldoActual', ''),
                    data.get('FecFinSaldoActual', '')
                ),
                self._font_color,
                'DINPro-Regular.otf',
                22,
                False
            )
        else:
            self._set_input_table(
                (500, 768),
                (
                    (
                        data.get('fondoOblInaf', ''),
                        data.get('aporteOblInaf', ''),
                        data.get('cargosOblInaf', ''),
                        data.get('rendimientoOblInaf', ''),
                        data.get('comisionOblInaf', ''),
                        data.get('saldoOblInaf', '')
                    ),
                    (
                        data.get('fondoOblAfec', ''),
                        data.get('aporteOblAfec', ''),
                        data.get('cargosOblAfec', ''),
                        data.get('rendimientoOblAfec', ''),
                        data.get('comisionOblAfec', ''),
                        data.get('saldoOblAfec', '')
                    )
                ),
                48
            )
            self._set_input_table(
                (488, 995),
                (
                    (
                        data.get('fondoVcf', ''),
                        data.get('aporteVcf', ''),
                        data.get('cargosVcf', ''),
                        data.get('rendimientoVcf', ''),
                        data.get('comisionVcf', ''),
                        data.get('saldoVcf', '')
                    ),
                    (
                        data.get('fondoVsf', ''),
                        data.get('aporteVsf', ''),
                        data.get('cargosVsf', ''),
                        data.get('rendimientoVsf', ''),
                        data.get('comisionVsf', ''),
                        data.get('saldoVsf', '')
                    )
                ),
                65
            )

            self._draw_text(
                self._front_draw_inst,
                (429, 1340),
                '(Del %s al %s)' % (
                    data.get('fecIniSaldoActual', ''),
                    data.get('FecFinSaldoActual', '')
                ),
                self._font_color,
                'DINPro-Regular.otf',
                22,
                False
            )

        _movements = [(
            line.get('fecMovim', ''),
            line.get('periodoDevengue', ''),
            line.get('tipoMovim', ''),
            line.get('conceptoMovim', ''),
            line.get('razonSocial', ''),
            line.get('montoMovim', '')
        ) for line in data.get('movimientosObl', [])]
        _movements += [(
            data.get('fecProcesoOblInaf', ''),
            data.get('mesRentabilidadOblInaf', ''),
            data.get('tipoAporteOblInaf', ''),
            data.get('tipoMovimOblInaf', ''),
            '',
            data.get('rendimientoPeriodoOblInaf', '')
        )]
        _movements += [(
            data.get('fecProcesoOblAfec', ''),
            data.get('mesRentabilidadOblAfec', ''),
            data.get('tipoAporteOblAfec', ''),
            data.get('tipoMovimOblAfec', ''),
            '',
            data.get('rendimientoPeriodoOblAfec', '')
        )]
        _movements += [(
            data.get('fecProcesoVcf', ''),
            data.get('mesRentabilidadVcf', ''),
            data.get('tipoAporteVcf', ''),
            data.get('tipoMovimVcf', ''),
            '',
            data.get('rendimientoPeriodoVcf', '')
        )]
        _movements += [(
            data.get('fecProcesoVsf', ''),
            data.get('mesRentabilidadVsf', ''),
            data.get('tipoAporteVsf', ''),
            data.get('tipoMovimVsf', ''),
            '',
            data.get('rendimientoPeriodoVsf', '')
        )]
        if self._ec_type == 'flujo':
            self._set_movements(
                (150, 1448),
                _movements
            )
            self._draw_text(
                self._front_draw_inst,
                (574, 1970),
                '(Del %s al %s)' % (
                    data.get('fecIniSaldoActual', ''),
                    data.get('fecFinSaldoActual', '')
                ),
                self._font_color,
                'DINPro-Regular.otf',
                22,
                False
            )
        else:
            self._set_movements(
                (150, 1458),
                _movements
            )
            self._draw_text(
                self._front_draw_inst,
                (574, 1980),
                '(Del %s al %s)' % (
                    data.get('fecIniSaldoActual', ''),
                    data.get('fecFinSaldoActual', '')
                ),
                self._font_color,
                'DINPro-Regular.otf',
                22,
                False
            )

        self._set_discount_table(
            (635, 2035),
            data.get('primaSeguroTotal', ''),
            data.get('comisionAfpTotal', '')
        )
        self._set_resume_table(
            (253, 2265),
            data.get('aporteSPP', ''),
            data.get('cargosSPP', ''),
            data.get('rendimientoSPP', ''),
            data.get('saldoSPP', '')
        )
        self._set_notes(
            (90, 940),
            list(filter(
                lambda x: x.get('grupoMensaje', '') == 'MENSAJES',
                data.get('mensajes')
            ))[0].get('mensajes')
        )
