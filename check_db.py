from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Karyawan

# Create engine
engine = create_engine('sqlite:///absensi.db')

# Create session
Session = sessionmaker(bind=engine)
session = Session()

# Query all employees
karyawan_list = session.query(Karyawan).all()

print("\n=== Data Karyawan ===")
print("Total Karyawan:", len(karyawan_list))
print("\nDetail Data:")
print("-" * 100)
for k in karyawan_list:
    print(f"ID: {k.id}")
    print(f"Nama: {k.nama}")
    print(f"Email: {k.email}")
    print(f"No. Telepon: {k.no_telepon}")
    print(f"Jabatan: {k.jabatan}")
    print(f"Departemen: {k.departemen}")
    print(f"Alamat: {k.alamat}")
    print(f"Tanggal Bergabung: {k.tanggal_bergabung}")
    print(f"Status: {'Aktif' if k.status else 'Tidak Aktif'}")
    print(f"Foto: {'Ada' if k.foto else 'Tidak Ada'}")
    print("-" * 100)

session.close() 