from tornado.httpclient import HTTPClient


masivo = (
    '186901LACIA3',
    '192510NSTTO6',
    '202911TAPNE7',
    '206290LTMAO8',
    '206881JBLAE2',
    '208391MMRDA0',
    '209661ERPRA2',
    '211831SZGAI6',
    '214231CZRAA9',
    '217710ISAIN9',
    '240131MMCBH0',
    '243350MSTAU0',
    '244011HTSST8',
    '253381TSCAZ6',
    '513531LJLAN2',
    '531700LNDEZ2'
)
pensionista = (
    '165961HCSCV7',
    '169481JHHRM0',
    '170011JPRCE6',
    '171381LSVOA7',
    '175511JFVUL4',
    '176631RBRAR1',
    '176811MCRAD1',
    '187841CALAA4',
    '188851RACAE5',
    '202530CTPAC9',
    '202761IHQCS8',
    '465701JMMQA4',
    '468111ARVLD7',
    '554230MMCES5',
    '557691DMCLL0',
    '586651WCMRT8'
)
premium = (
    '194241RCSAE8',
    '201481FLDIZ6',
    '210731JMSII3',
    '223691JGCEP0',
    '243681ESHNR1',
    '253031ACGRS4',
    '258381MCGHM4',
    '312571DJAUN5',
    '503471CPQH%C3%B17',
    '513231HMZEA0',
    '529551EAAPZ7',
    '551321JRADR5',
    '555781GLCRT0',
    '568720MFGUA6',
    '595370ERSEC3',
    '599981CLRER0'
)
voluntario = (
    '220441ADSIV6',
    '534571JQOSR0',
    '547690KMBEL4',
    '561061GAVAQ8',
    '610401ECVDL2'
)
data = voluntario

client = HTTPClient()
for ec in data:
    req = client.fetch('http://127.0.0.1:8888/view?docNumber=' + ec)
    with open(ec + '.pdf', 'wb+') as f:
        f.write(req.body)

