"""Detiene los escritores locales y respalda datos para migrarlos sin eliminar volúmenes."""
import argparse
import gzip
import json
from pathlib import Path
import shutil
import subprocess

DEPLOY = Path(__file__).resolve().parents[1]


def snapshot(directory):
    root = Path(directory).resolve() / 'backups'
    root.mkdir(parents=True, exist_ok=True)
    if (root / 'mysql.sql.gz').exists():
        raise ValueError('Ya hay un respaldo de migración; no se sobrescribe.')
    command = ['docker', 'compose', '--env-file', str(DEPLOY / 'target/local/runtime.env'),
               '-f', str(DEPLOY / 'docker-compose.yml'), '-f', str(DEPLOY / 'docker-compose.local.yml'),
               '-p', 'logitrack-local-local', 'stop', 'frontend', 'api-gateway', 'security-service',
               'courier-service', 'shipment-service', 'grafana', 'prometheus']
    subprocess.run(command, check=True)
    sql = "SELECT JSON_OBJECT('customers',(SELECT COUNT(*) FROM logitrack.customers),'shipments',(SELECT COUNT(*) FROM logitrack.shipments),'couriers',(SELECT COUNT(*) FROM courier_db.couriers),'users',(SELECT COUNT(*) FROM security_db.users));"
    counts = subprocess.check_output(['docker','exec','logitrack-mysql','sh','-c',
        'export MYSQL_PWD="$MYSQL_ROOT_PASSWORD"; exec mysql -uroot -N -B -e "$1"', 'counts', sql], text=True)
    (root / 'counts-before.json').write_text(json.dumps(json.loads(counts), indent=2), encoding='utf-8')
    process = subprocess.Popen(['docker', 'exec', 'logitrack-mysql', 'sh', '-c',
        'export MYSQL_PWD="$MYSQL_ROOT_PASSWORD"; exec mysqldump -uroot --single-transaction --routines --triggers --events --set-gtid-purged=OFF --no-tablespaces --databases security_db courier_db logitrack shipment_db'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    with gzip.open(root / 'mysql.sql.gz', 'wb') as output:
        shutil.copyfileobj(process.stdout, output)
    if process.wait() != 0:
        raise RuntimeError('Falló el respaldo SQL. Los volúmenes locales se conservan.')
    for service, path in [('grafana','/var/lib/grafana/.'),('prometheus','/prometheus/.')]:
        with (root / (service + '.tar')).open('wb') as output:
            subprocess.run(['docker','cp',f'logitrack-{service}:{path}','-'], stdout=output, check=True)
    print('Respaldo SQL y datos de observabilidad guardados. Los volúmenes locales no se borraron.')
    print('Conteos de migración: ' + counts.strip())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', required=True)
    snapshot(parser.parse_args().directory)
