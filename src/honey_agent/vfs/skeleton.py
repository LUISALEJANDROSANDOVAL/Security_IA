"""
src/honey_agent/vfs/skeleton.py
Dueño: Programador 1 (P1).
Responsabilidad: Poblar el VFS inicial con archivos idénticos a Ubuntu 22.04 LTS.
"""

from honey_agent.vfs.in_memory_tree import VirtualFileSystem

def populate_ubuntu_skeleton(vfs: VirtualFileSystem):
    """Puebla el árbol VFS en RAM con el esqueleto del sistema operativo."""
    # 1. Directorios base de la jerarquía FHS (Filesystem Hierarchy Standard)
    standard_dirs = [
        "/bin", "/boot", "/dev", "/etc", "/home", "/lib", "/lib64", 
        "/media", "/mnt", "/opt", "/proc", "/root", "/run", "/sbin", 
        "/srv", "/sys", "/tmp", "/usr", "/usr/bin", "/usr/sbin", 
        "/var", "/var/www", "/var/www/html", "/var/log", "/etc/ssh", 
        "/home/ubuntu", "/root/.ssh"
    ]
    for d in standard_dirs:
        vfs.mkdir(d)

    # 2. Información del sistema operativo (/etc/os-release)
    vfs.write_file(
        "/etc/os-release",
        (
            'NAME="Ubuntu"\n'
            'VERSION="22.04.4 LTS (Jammy Jellyfish)"\n'
            'ID=ubuntu\n'
            'ID_LIKE=debian\n'
            'PRETTY_NAME="Ubuntu 22.04.4 LTS"\n'
            'VERSION_ID="22.04"\n'
            'HOME_URL="https://www.ubuntu.com/"\n'
            'SUPPORT_URL="https://help.ubuntu.com/"\n'
            'BUG_REPORT_URL="https://bugs.launchpad.net/ubuntu/"\n'
            'PRIVACY_POLICY_URL="https://www.ubuntu.com/legal/terms-and-policies/privacy-policy"\n'
            'UBUNTU_CODENAME=jammy\n'
        ).encode("utf-8")
    )

    # 3. Hostname y resolución de red
    vfs.write_file("/etc/hostname", b"prod-srv-app01\n")
    vfs.write_file(
        "/etc/hosts",
        (
            "127.0.0.1 localhost\n"
            "127.0.1.1 prod-srv-app01\n"
            "# The following lines are desirable for IPv6 capable hosts\n"
            "::1 ip6-localhost ip6-loopback\n"
            "fe00::0 ip6-localnet\n"
            "ff00::0 ip6-mcastprefix\n"
            "ff02::1 ip6-allnodes\n"
            "ff02::2 ip6-allrouters\n"
        ).encode("utf-8")
    )
    vfs.write_file(
        "/etc/resolv.conf",
        (
            "# This file is managed by man:systemd-resolved(8).\n"
            "nameserver 127.0.0.53\n"
            "options edns0 trust-ad\n"
            "search corp.internal\n"
        ).encode("utf-8")
    )

    # 4. Cuentas de usuario (/etc/passwd)
    vfs.write_file(
        "/etc/passwd",
        (
            "root:x:0:0:root:/root:/bin/bash\n"
            "daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\n"
            "bin:x:2:2:bin:/bin:/usr/sbin/nologin\n"
            "sys:x:3:3:sys:/dev:/usr/sbin/nologin\n"
            "sync:x:4:65534:sync:/bin:/bin/sync\n"
            "games:x:5:60:games:/usr/games:/usr/sbin/nologin\n"
            "man:x:6:12:man:/var/cache/man:/usr/sbin/nologin\n"
            "lp:x:7:7:lp:/var/spool/lpd:/usr/sbin/nologin\n"
            "mail:x:8:8:mail:/var/mail:/usr/sbin/nologin\n"
            "news:x:9:9:news:/var/spool/news:/usr/sbin/nologin\n"
            "uucp:x:10:10:uucp:/var/spool/uucp:/usr/sbin/nologin\n"
            "proxy:x:13:13:proxy:/bin:/usr/sbin/nologin\n"
            "www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin\n"
            "backup:x:34:34:backup:/var/backups:/usr/sbin/nologin\n"
            "list:x:38:38:Mailing List Manager:/var/list:/usr/sbin/nologin\n"
            "irc:x:39:39:ircd:/run/ircd:/usr/sbin/nologin\n"
            "nobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin\n"
            "systemd-network:x:100:102:systemd Network Management,,,:/run/systemd:/usr/sbin/nologin\n"
            "systemd-resolve:x:101:103:systemd Resolver,,,:/run/systemd:/usr/sbin/nologin\n"
            "messagebus:x:102:105::/nonexistent:/usr/sbin/nologin\n"
            "sshd:x:121:65534::/run/sshd:/usr/sbin/nologin\n"
            "ubuntu:x:1000:1000:Ubuntu:/home/ubuntu:/bin/bash\n"
        ).encode("utf-8")
    )

    # 5. Entorno /proc simulado
    vfs.write_file(
        "/proc/version",
        b"Linux version 5.15.0-101-generic (buildd@lcy02-amd64-022) (gcc 11.4.0) #111-Ubuntu SMP Tue Mar 5 20:16:58 UTC 2024\n"
    )
    vfs.write_file(
        "/proc/cpuinfo",
        (
            "processor\t: 0\n"
            "vendor_id\t: GenuineIntel\n"
            "cpu family\t: 6\n"
            "model\t\t: 158\n"
            "model name\t: Intel(R) Xeon(R) Platinum 8275CL CPU @ 3.00GHz\n"
            "stepping\t: 7\n"
            "cpu MHz\t\t: 2999.998\n"
            "cache size\t: 36608 KB\n"
        ).encode("utf-8")
    )

    # 6. Servicio Web señuelo
    vfs.write_file(
        "/var/www/html/index.nginx-debian.html",
        (
            "<!DOCTYPE html>\n"
            "<html>\n"
            "<head>\n"
            "<title>Welcome to nginx!</title>\n"
            "<style>body { width: 35em; margin: 0 auto; font-family: Tahoma, Verdana, Arial, sans-serif; }</style>\n"
            "</head>\n"
            "<body>\n"
            "<h1>Welcome to nginx!</h1>\n"
            "<p>If you see this page, the nginx web server is successfully installed and working.</p>\n"
            "</body>\n"
            "</html>\n"
        ).encode("utf-8")
    )
