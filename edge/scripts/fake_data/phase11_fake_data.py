import argparse
import json
import random
import sqlite3
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

try:
    import paho.mqtt.client as mqtt
except Exception:
    mqtt = None


def now_iso():
    return datetime.now().replace(microsecond=0).isoformat()


def edge_root():
    return Path(__file__).resolve().parents[2]


def db_path():
    return edge_root() / "database" / "smart_home_edge.db"


def post_json(base_url, path, payload):
    url = base_url.rstrip("/") + path
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=8) as res:
            body = res.read().decode("utf-8")
            return res.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = body
        return e.code, parsed
    except Exception as e:
        return 0, str(e)


def publish_mqtt(host, port, topic, payload):
    if mqtt is None:
        return False, "paho-mqtt not installed"

    try:
        client = mqtt.Client()
        client.connect(host, port, 60)
        client.loop_start()
        info = client.publish(topic, json.dumps(payload), qos=0)
        info.wait_for_publish()
        client.loop_stop()
        client.disconnect()
        return True, "published"
    except Exception as e:
        return False, str(e)


def ensure_logs_table(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            home_id INTEGER,
            timestamp TEXT,
            severity TEXT,
            home TEXT,
            event_type TEXT,
            details TEXT,
            action_taken TEXT
        )
        """
    )
    conn.commit()


def table_columns(conn, table):
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [row[1] for row in rows]


def insert_log(conn, home_id, severity, home, event_type, details, action_taken):
    ensure_logs_table(conn)
    columns = table_columns(conn, "system_logs")

    data = {
        "home_id": home_id,
        "timestamp": now_iso(),
        "created_at": now_iso(),
        "severity": severity,
        "level": severity,
        "home": home,
        "home_name": home,
        "event_type": event_type,
        "type": event_type,
        "details": details,
        "message": details,
        "action_taken": action_taken,
        "action": action_taken,
    }

    selected = [(col, data[col]) for col in columns if col != "id" and col in data]

    if not selected:
        return False

    names = ", ".join(col for col, _ in selected)
    marks = ", ".join("?" for _ in selected)
    values = [value for _, value in selected]

    conn.execute(f"INSERT INTO system_logs ({names}) VALUES ({marks})", values)
    conn.commit()
    return True


def home_label(home_code):
    digits = "".join(ch for ch in home_code if ch.isdigit()).lstrip("0")
    if digits:
        return f"Apartment {digits}"
    return home_code


def fallback_device_id(prefix, home_code):
    return f"{prefix}-{home_code}-001"


def extract_device(body, fallback_id, fallback_token=None):
    device = {}

    if isinstance(body, dict):
        if isinstance(body.get("device"), dict):
            device = body["device"]
        else:
            device = body

    return {
        "id": device.get("id"),
        "device_id": device.get("device_id") or fallback_id,
        "device_token": device.get("device_token") or fallback_token,
        "mqtt_topic": device.get("mqtt_topic"),
    }


def claim_device(base_url, claim_code, device_type, ip, mac, fallback_id):
    payload = {
        "claim_code": claim_code,
        "device_type": device_type,
        "device_ip": ip,
        "mac_address": mac,
        "firmware_version": "fake-1.0",
    }

    status, body = post_json(base_url, "/api/devices/claim", payload)
    device = extract_device(body, fallback_id)

    print(f"CLAIM {fallback_id}: {status}")
    print(body)

    return device


def heartbeat_device(base_url, device, ip, mac):
    payload = {
        "device_id": device["device_id"],
        "device_ip": ip,
        "mac_address": mac,
        "status": "online",
        "firmware_version": "fake-1.0",
    }

    if device.get("device_token"):
        payload["device_token"] = device["device_token"]

    status, body = post_json(base_url, "/api/devices/heartbeat", payload)

    print(f"HEARTBEAT {device['device_id']}: {status}")
    print(body)

    return status, body


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--home-code", default="HOME008")
    parser.add_argument("--home-id", type=int, default=1)
    parser.add_argument("--door-claim", default="HOME008-NJZP")
    parser.add_argument("--energy-claim", default="HOME008-R4HL")
    parser.add_argument("--door-ip", default="192.168.1.88")
    parser.add_argument("--energy-ip", default="192.168.1.90")
    parser.add_argument("--door-mac", default="AA:BB:CC:DD:EE:FF")
    parser.add_argument("--energy-mac", default="11:22:33:44:55:66")
    parser.add_argument("--mqtt-host", default="127.0.0.1")
    parser.add_argument("--mqtt-port", type=int, default=1883)
    parser.add_argument("--count", type=int, default=3)
    parser.add_argument("--interval", type=float, default=1.0)
    args = parser.parse_args()

    home = home_label(args.home_code)
    db = db_path()

    print(f"DB: {db}")

    if db.exists():
        conn = sqlite3.connect(db)
        insert_log(conn, args.home_id, "INFO", home, "Fake Data", "Phase 11 fake data started", "Ready")
        conn.close()
        print("LOCAL LOG SEEDED")
    else:
        print("DB NOT FOUND")

    door = claim_device(
        args.base_url,
        args.door_claim,
        "smart_door",
        args.door_ip,
        args.door_mac,
        fallback_device_id("DOOR", args.home_code),
    )

    energy = claim_device(
        args.base_url,
        args.energy_claim,
        "energy_monitor",
        args.energy_ip,
        args.energy_mac,
        fallback_device_id("METER", args.home_code),
    )

    heartbeat_device(args.base_url, door, args.door_ip, args.door_mac)
    heartbeat_device(args.base_url, energy, args.energy_ip, args.energy_mac)

    for index in range(args.count):
        watts = random.randint(350, 1800)
        payload = {
            "home_code": args.home_code,
            "home_id": args.home_id,
            "device_id": energy["device_id"],
            "watts": watts,
            "voltage": 220,
            "current": round(watts / 220, 2),
            "kwh_today": round(random.uniform(1.2, 6.5), 2),
            "timestamp": now_iso(),
            "source": "phase11_fake_data",
        }

        ok, msg = publish_mqtt(args.mqtt_host, args.mqtt_port, "home/energy", payload)
        print(f"MQTT home/energy: {ok} {msg}")

        status_payload = {
            "home_code": args.home_code,
            "device_id": energy["device_id"],
            "status": "online",
            "timestamp": now_iso(),
            "source": "phase11_fake_data",
        }

        ok, msg = publish_mqtt(args.mqtt_host, args.mqtt_port, f"device/{energy['device_id']}/status", status_payload)
        print(f"MQTT device status: {ok} {msg}")

        if db.exists():
            conn = sqlite3.connect(db)
            insert_log(
                conn,
                args.home_id,
                "INFO",
                home,
                "Energy Reading",
                f"Fake energy reading received: {watts} W",
                "Stored",
            )
            conn.close()

        time.sleep(args.interval)

    if db.exists():
        conn = sqlite3.connect(db)
        insert_log(conn, args.home_id, "INFO", home, "Fake Data", "Phase 11 fake data completed", "Done")
        conn.close()

    print("PHASE 11 FAKE DATA DONE")


if __name__ == "__main__":
    main()