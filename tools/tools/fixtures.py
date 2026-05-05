system_fixtures = [
    'auth.user',
]

docca_fixtures = [
    'docca.doctag',
    'docca.docendpoint',
    'docca.docparameterdef',
    'docca.docparameter',
    'docca.docresponsefield',
]

reggi_fixtures = [
    'reggi.userprofile',
    'reggi.apikey',
]

kotta_fixtures = [
    'kotta.tier',
    'kotta.endpoint',
    'kotta.tierendpointlimit',
    'kotta.usertier',
    'kotta.usagecounter',
]

billa_fixtures = [
    'billa.creditpack',
    'billa.creditbalance',
    'billa.purchase',
]

fixtures = system_fixtures + docca_fixtures + reggi_fixtures + kotta_fixtures + billa_fixtures
