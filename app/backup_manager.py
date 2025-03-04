import os
import shutil
from datetime import datetime
import pandas as pd
from pathlib import Path

class BackupManager:
    def __init__(self, drive_manager, backup_folder="backups"):
        self.drive_manager = drive_manager
        self.backup_folder = backup_folder
        self.local_backup_path = Path("data") / backup_folder
        self.ensure_backup_folders()

    def ensure_backup_folders(self):
        """Asegura que existan las carpetas necesarias para los backups"""
        if not os.path.exists(self.local_backup_path):
            os.makedirs(self.local_backup_path)

    def create_backup(self):
        """Crea una copia de seguridad de los archivos de datos"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Lista de archivos a respaldar
        files_to_backup = ['transactions.csv', 'balance.csv']
        
        backup_info = {
            'timestamp': timestamp,
            'files': [],
            'status': 'success'
        }

        try:
            for file_name in files_to_backup:
                source_path = Path("data") / file_name
                if source_path.exists():
                    # Crear nombre del archivo de backup
                    backup_filename = f"{file_name.split('.')[0]}_{timestamp}.csv"
                    backup_path = self.local_backup_path / backup_filename

                    # Hacer copia local
                    shutil.copy2(source_path, backup_path)

                    # Si hay conexión a Drive, subir también allí
                    if self.drive_manager.service:
                        try:
                            with open(backup_path, 'rb') as f:
                                df = pd.read_csv(f)
                                self.drive_manager.save_data(
                                    df,
                                    f"backups/{backup_filename}"
                                )
                            backup_info['files'].append({
                                'name': file_name,
                                'backup_name': backup_filename,
                                'drive_sync': True
                            })
                        except Exception as e:
                            backup_info['files'].append({
                                'name': file_name,
                                'backup_name': backup_filename,
                                'drive_sync': False,
                                'error': str(e)
                            })
                    else:
                        backup_info['files'].append({
                            'name': file_name,
                            'backup_name': backup_filename,
                            'drive_sync': False
                        })

        except Exception as e:
            backup_info['status'] = 'error'
            backup_info['error'] = str(e)

        return backup_info

    def list_backups(self):
        """Lista todos los backups disponibles"""
        backups = []
        if os.path.exists(self.local_backup_path):
            for file in os.listdir(self.local_backup_path):
                if file.endswith('.csv'):
                    file_path = self.local_backup_path / file
                    backups.append({
                        'filename': file,
                        'date': datetime.fromtimestamp(os.path.getmtime(file_path)),
                        'size': os.path.getsize(file_path)
                    })
        
        return sorted(backups, key=lambda x: x['date'], reverse=True)

    def restore_backup(self, backup_filename):
        """Restaura un backup específico"""
        backup_path = self.local_backup_path / backup_filename
        if not backup_path.exists():
            raise FileNotFoundError(f"No se encontró el archivo de backup: {backup_filename}")

        # Extraer el nombre original del archivo
        original_name = backup_filename.split('_')[0] + '.csv'
        destination_path = Path("data") / original_name

        try:
            shutil.copy2(backup_path, destination_path)
            return True
        except Exception as e:
            raise Exception(f"Error al restaurar el backup: {str(e)}")
