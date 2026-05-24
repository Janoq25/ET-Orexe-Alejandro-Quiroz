#!/usr/bin/env python3
"""Verifica que ansible_test_user puede conectarse a MySQL y ejecutar SELECT 1."""

import argparse
import sys

import pymysql


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Valida la conexión de ansible_test_user a Percona Server."
    )
    parser.add_argument(
        "--host",
        default="10.85.24.12",
        help="IP o hostname del servidor MySQL (default: IP de servidor-orexe)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3306,
        help="Puerto MySQL (default: 3306)",
    )
    parser.add_argument(
        "--user",
        default="ansible_test_user",
        help="Usuario MySQL (default: ansible_test_user)",
    )
    parser.add_argument(
        "--password",
        required=True,
        help="Contraseña del usuario MySQL",
    )
    return parser.parse_args()


def verify_connection(host: str, port: int, user: str, password: str) -> None:
    print(f"Conectando a MySQL en {host}:{port} como '{user}'...")

    connection = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        connect_timeout=10,
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()

        if result != (1,):
            print(f"ERROR: SELECT 1 devolvió un resultado inesperado: {result}")
            sys.exit(1)

        print("OK: Conexión exitosa. SELECT 1 ejecutado correctamente.")
    finally:
        connection.close()


def main() -> None:
    args = parse_args()

    try:
        verify_connection(args.host, args.port, args.user, args.password)
    except pymysql.MySQLError as exc:
        print(f"ERROR: No se pudo conectar o ejecutar la consulta: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
