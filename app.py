from flask import Flask, render_template, request, send_file, redirect, url_for, flash, session
import os
from werkzeug.utils import secure_filename
from PIL import Image
from kompresi.rle import rle_compress
from kompresi.huffman import huffman_compress
import zipfile
import io
import pikepdf
import subprocess
import shutil
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'pdf', 'docx', 'xlsx', 'pptx'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER
app.secret_key = 'supersecretkey'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_compression_settings(level):
    """Get compression settings based on level"""
    settings = {
        'small': {
            'image_quality': 70,  # Kurangi dari 85 ke 70 untuk kompresi yang lebih efektif
            'image_max_size': (1600, 1200),  # Kurangi ukuran maksimal untuk kompresi yang lebih efektif
            'office_image_quality': 70,  # Sesuaikan dengan image_quality
            'office_image_max_size': (1600, 1200),  # Sesuaikan dengan image_max_size
            'pdf_quality': 'printer',
            'zip_compression': 6
        },
        'medium': {
            'image_quality': 75,
            'image_max_size': (1280, 720),
            'office_image_quality': 70,
            'office_image_max_size': (1280, 720),
            'pdf_quality': 'ebook',
            'zip_compression': 8
        },
        'large': {
            'image_quality': 60,
            'image_max_size': (800, 600),
            'office_image_quality': 60,
            'office_image_max_size': (800, 600),
            'pdf_quality': 'screen',
            'zip_compression': 9
        }
    }
    return settings.get(level, settings['medium'])

def clean_image_metadata(img, compression_level='medium'):
    """Membersihkan metadata gambar untuk kompresi yang lebih efektif"""
    try:
        # Untuk kompresi kecil, pertahankan metadata penting
        if compression_level == 'small':
            # Hanya hapus metadata yang tidak penting
            if hasattr(img, 'info'):
                # Hapus metadata yang tidak diperlukan
                metadata_to_remove = ['exif', 'icc_profile', 'dpi', 'comment']
                for key in metadata_to_remove:
                    if key in img.info:
                        del img.info[key]
        else:
            # Untuk medium dan large, hapus semua metadata
            if hasattr(img, 'info'):
                img.info.clear()
        
        return img
    except Exception as e:
        logger.warning(f"Error cleaning metadata: {e}")
        return img

def optimize_jpeg_compression(img, quality, compression_level='medium'):
    """Optimasi khusus untuk kompresi JPEG"""
    try:
        if compression_level == 'small':
            # Untuk kompresi kecil, gunakan pengaturan yang lebih agresif untuk pengurangan ukuran
            return {
                'quality': 70,  # Kualitas lebih rendah untuk kompresi yang lebih efektif
                'optimize': True,
                'progressive': True,
                'subsampling': 1,  # Standard chroma subsampling untuk kompresi
                'dpi': (72, 72),   # Standard DPI
                'exif': None       # Remove EXIF data for smaller size
            }
        elif compression_level == 'medium':
            return {
                'quality': quality,
                'optimize': True,
                'progressive': True,
                'subsampling': 1   # Standard chroma subsampling
            }
        else:  # large
            return {
                'quality': quality,
                'optimize': True,
                'subsampling': 2   # Aggressive chroma subsampling
            }
    except Exception as e:
        logger.warning(f"Error in JPEG optimization: {e}")
        return {'quality': quality, 'optimize': True}

def compress_image(filepath, outdir, compression_level='medium'):
    """Kompresi gambar dengan pengaturan berdasarkan level"""
    try:
        settings = get_compression_settings(compression_level)
        logger.info(f"Compressing image with level: {compression_level}, quality: {settings['image_quality']}")
        
        img = Image.open(filepath)
        original_size = img.size
        
        # Convert to RGB if necessary for JPEG
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Bersihkan metadata
        img = clean_image_metadata(img, compression_level)
        
        # Logika resize yang lebih cerdas untuk kompresi kecil
        if compression_level == 'small':
            # Untuk kompresi kecil, resize lebih agresif untuk mendapatkan pengurangan ukuran
            ext = filepath.split('.')[-1].lower()
            if ext in ['jpg', 'jpeg']:
                # Untuk JPEG, resize lebih agresif untuk kompresi kecil
                max_dimension = 1600  # Kurangi dari 2048 ke 1600 untuk kompresi yang lebih efektif
                if img.size[0] > max_dimension or img.size[1] > max_dimension:
                    # Resize dengan mempertahankan aspect ratio
                    img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
                    logger.info(f"Resized JPEG from {original_size} to {img.size} for small compression (aggressive)")
                else:
                    # Jika ukuran sudah kecil, resize sedikit untuk kompresi tambahan
                    if img.size[0] > 1200 or img.size[1] > 1200:
                        img.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
                        logger.info(f"Resized JPEG from {original_size} to {img.size} for small compression (moderate)")
            else:
                # Untuk format lain, resize jika lebih dari 2048px
                max_dimension = 2048
                if img.size[0] > max_dimension or img.size[1] > max_dimension:
                    img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
                    logger.info(f"Resized from {original_size} to {img.size} for small compression")
        elif compression_level == 'medium':
            # Untuk medium, resize jika lebih dari 1024px
            if img.size[0] > settings['image_max_size'][0] or img.size[1] > settings['image_max_size'][1]:
                img.thumbnail(settings['image_max_size'], Image.Resampling.LANCZOS)
                logger.info(f"Resized from {original_size} to {img.size} for medium compression")
        else:  # large
            # Untuk large, resize sesuai pengaturan
            if img.size[0] > settings['image_max_size'][0] or img.size[1] > settings['image_max_size'][1]:
                img.thumbnail(settings['image_max_size'], Image.Resampling.LANCZOS)
                logger.info(f"Resized from {original_size} to {img.size} for large compression")
        
        outname = os.path.basename(filepath)
        outpath = os.path.join(outdir, outname)
        
        # Determine format and save with optimized settings
        ext = outname.lower().split('.')[-1]
        
        if ext in ['jpg', 'jpeg']:
            # Optimasi khusus untuk JPEG pada skala kecil
            if compression_level == 'small':
                # Untuk kompresi kecil, gunakan kualitas yang lebih rendah untuk pengurangan ukuran yang lebih efektif
                img.save(outpath, 'JPEG', 
                        quality=70,  # Kurangi kualitas dari 85 ke 70
                        optimize=True, 
                        progressive=True,
                        subsampling=1,  # Standard chroma subsampling
                        dpi=(72, 72))   # Standard DPI
                logger.info(f"JPEG compressed with small scale settings: quality=70, progressive=True")
            else:
                # Gunakan optimasi khusus untuk JPEG pada skala lain
                jpeg_settings = optimize_jpeg_compression(img, settings['image_quality'], compression_level)
                img.save(outpath, 'JPEG', **jpeg_settings)
                
        elif ext == 'png':
            if compression_level == 'small':
                # Untuk kompresi kecil, gunakan kompresi yang seimbang
                img.save(outpath, 'PNG', 
                        optimize=True, 
                        compress_level=6,  # Level 6 untuk keseimbangan
                        bits=8)  # 8-bit untuk kompresi yang lebih baik
            else:
                img.save(outpath, 'PNG', optimize=True, compress_level=9)
                
        elif ext == 'gif':
            if compression_level == 'small':
                # Untuk GIF, gunakan optimasi yang lebih halus
                img.save(outpath, 'GIF', optimize=True, duration=100)
            else:
                img.save(outpath, 'GIF', optimize=True)
                
        elif ext == 'bmp':
            # BMP tidak bisa dikompresi, jadi konversi ke PNG untuk kompresi kecil
            if compression_level == 'small':
                png_path = outpath.replace('.bmp', '.png')
                img.save(png_path, 'PNG', optimize=True, compress_level=6)
                logger.info(f"Converted BMP to PNG for better compression: {png_path}")
                return png_path
            else:
                img.save(outpath, 'BMP')
        else:
            # Format lain, gunakan pengaturan default
            img.save(outpath, quality=settings['image_quality'], optimize=True)
        
        logger.info(f"Image compressed successfully: {outpath}")
        return outpath
        
    except Exception as e:
        logger.error(f"Error compressing image: {e}")
        # Fallback: copy original file
        outname = os.path.basename(filepath)
        outpath = os.path.join(outdir, outname)
        shutil.copy2(filepath, outpath)
        return outpath

def compress_document(filepath, outdir):
    outname = os.path.splitext(os.path.basename(filepath))[0] + '.zip'
    outpath = os.path.join(outdir, outname)
    with zipfile.ZipFile(outpath, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(filepath, arcname=os.path.basename(filepath))
    return outpath

def compress_pdf(filepath, outdir):
    outname = os.path.basename(filepath)
    outpath = os.path.join(outdir, outname)
    pdf = pikepdf.open(filepath)
    pdf.save(outpath)
    pdf.close()
    return outpath

def compress_pdf_ghostscript(filepath, outdir, compression_level='medium'):
    """Kompresi PDF menggunakan Ghostscript dengan fallback"""
    try:
        settings = get_compression_settings(compression_level)
        logger.info(f"Compressing PDF with level: {compression_level}, quality: {settings['pdf_quality']}")
        
        # Check if Ghostscript is available
        gs_paths = [
            r'C:\Program Files\gs\gs10.05.1\bin\gswin64c.exe',
            r'C:\Program Files\gs\gs10.04.0\bin\gswin64c.exe',
            r'C:\Program Files\gs\gs10.03.0\bin\gswin64c.exe',
            'gs',  # If in PATH
            'gswin64c'  # Alternative name
        ]
        
        gs_exe = None
        for path in gs_paths:
            try:
                subprocess.run([path, '--version'], capture_output=True, check=True)
                gs_exe = path
                break
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        if gs_exe:
            outname = os.path.basename(filepath)
            outpath = os.path.join(outdir, outname)
            
            # Pengaturan khusus untuk level kompresi
            if compression_level == 'small':
                # Untuk kompresi kecil, gunakan pengaturan yang lebih halus
                gs_command = [
                    gs_exe,
                    '-sDEVICE=pdfwrite',
                    '-dCompatibilityLevel=1.7',  # Versi yang lebih baru
                    f'-dPDFSETTINGS=/{settings["pdf_quality"]}',
                    '-dColorImageDownsampleType=/Bicubic',  # Metode downsampling yang lebih halus
                    '-dColorImageResolution=150',  # Resolusi yang lebih tinggi
                    '-dGrayImageDownsampleType=/Bicubic',
                    '-dGrayImageResolution=150',
                    '-dMonoImageDownsampleType=/Bicubic',
                    '-dMonoImageResolution=150',
                    '-dNOPAUSE',
                    '-dQUIET',
                    '-dBATCH',
                    f'-sOutputFile={outpath}',
                    filepath
                ]
            else:
                # Pengaturan standar untuk medium dan large
                gs_command = [
                    gs_exe,
                    '-sDEVICE=pdfwrite',
                    '-dCompatibilityLevel=1.4',
                    f'-dPDFSETTINGS=/{settings["pdf_quality"]}',
                    '-dNOPAUSE',
                    '-dQUIET',
                    '-dBATCH',
                    f'-sOutputFile={outpath}',
                    filepath
                ]
            
            subprocess.run(gs_command, check=True, capture_output=True)
            logger.info(f"PDF compressed with Ghostscript: {outpath}")
            return outpath
        else:
            logger.warning("Ghostscript not found, using pikepdf fallback")
            return compress_pdf_pikepdf(filepath, outdir, compression_level)
            
    except Exception as e:
        logger.error(f"Error compressing PDF with Ghostscript: {e}")
        return compress_pdf_pikepdf(filepath, outdir, compression_level)

def compress_pdf_pikepdf(filepath, outdir, compression_level='medium'):
    """Fallback PDF compression using pikepdf"""
    try:
        logger.info("Using pikepdf for PDF compression")
        outname = os.path.basename(filepath)
        outpath = os.path.join(outdir, outname)
        
        pdf = pikepdf.open(filepath)
        pdf.save(outpath, recompress_flate=True, object_stream_mode=pikepdf.ObjectStreamMode.generate)
        pdf.close()
        
        logger.info(f"PDF compressed with pikepdf: {outpath}")
        return outpath
    except Exception as e:
        logger.error(f"Error compressing PDF with pikepdf: {e}")
        # Final fallback: copy original
        outname = os.path.basename(filepath)
        outpath = os.path.join(outdir, outname)
        shutil.copy2(filepath, outpath)
        return outpath

def compress_office_with_libreoffice(filepath, outdir):
    soffice_path = r'C:\Program Files\LibreOffice\program\soffice.exe'
    outname = os.path.basename(filepath)
    out_ext = outname.split('.')[-1]
    # Output sementara ke ODT/ODS/ODP jika format docx/xlsx/pptx
    convert_map = {'docx': 'odt', 'xlsx': 'ods', 'pptx': 'odp'}
    target_ext = convert_map.get(out_ext, out_ext)
    try:
        result = subprocess.run(
            [
                soffice_path, '--headless', '--convert-to', target_ext, '--outdir', outdir, filepath
            ],
            check=True,
            capture_output=True,
            text=True
        )
        print('LibreOffice output:', result.stdout, result.stderr)
        # Cari file hasil konversi
        base = os.path.splitext(outname)[0]
        converted_file = os.path.join(outdir, f'{base}.{target_ext}')
        if os.path.exists(converted_file):
            return converted_file
        else:
            raise FileNotFoundError('File hasil konversi tidak ditemukan.')
    except subprocess.CalledProcessError as e:
        print('LibreOffice error:', e.stdout, e.stderr)
        raise RuntimeError('Konversi dengan LibreOffice gagal. Cek file dan formatnya.')

def compress_office_images(filepath, outdir, office_type, compression_level='medium'):
    """Kompresi file Office dengan kompresi gambar internal"""
    try:
        settings = get_compression_settings(compression_level)
        logger.info(f"Compressing {office_type} with level: {compression_level}")
        
        outname = os.path.basename(filepath)
        outpath = os.path.join(outdir, outname)
        temp_dir = f'temp_{office_type}_{os.getpid()}'
        
        # Extract office file
        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Find media directory based on office type
        media_paths = {
            'docx': os.path.join(temp_dir, 'word', 'media'),
            'pptx': os.path.join(temp_dir, 'ppt', 'media'),
            'xlsx': os.path.join(temp_dir, 'xl', 'media')
        }
        
        media_path = media_paths.get(office_type)
        compressed_images = 0
        
        if media_path and os.path.exists(media_path):
            for img_name in os.listdir(media_path):
                img_path = os.path.join(media_path, img_name)
                try:
                    img = Image.open(img_path)
                    original_size = img.size
                    
                    # Convert to RGB if necessary
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')
                    
                    # Bersihkan metadata
                    img = clean_image_metadata(img, compression_level)
                    
                    # Logika resize yang benar untuk setiap level
                    if office_type == 'docx':
                        # Untuk Word, kompresi yang lebih efektif pada semua skala
                        if compression_level == 'small':
                            # Skala kecil = kompresi sedang (resize ke 1600px)
                            max_dimension = 1600
                            if img.size[0] > max_dimension or img.size[1] > max_dimension:
                                img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
                                logger.info(f"Resized Word image from {original_size} to {img.size} for small compression (moderate)")
                        elif compression_level == 'medium':
                            # Skala sedang = kompresi agresif (resize ke 1200px)
                            max_dimension = 1200
                            if img.size[0] > max_dimension or img.size[1] > max_dimension:
                                img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
                                logger.info(f"Resized Word image from {original_size} to {img.size} for medium compression (aggressive)")
                        else:  # large
                            # Skala besar = kompresi maksimal (resize ke 800px)
                            max_dimension = 800
                            if img.size[0] > max_dimension or img.size[1] > max_dimension:
                                img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
                                logger.info(f"Resized Word image from {original_size} to {img.size} for large compression (maximum)")
                    else:
                        # Untuk file lain (Excel, PowerPoint), gunakan logika normal
                        if compression_level == 'small':
                            # Untuk kompresi kecil, resize jika lebih dari 2048px
                            max_dimension = 2048
                            if img.size[0] > max_dimension or img.size[1] > max_dimension:
                                img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
                                logger.info(f"Resized office image from {original_size} to {img.size} for small compression")
                        elif compression_level == 'medium':
                            # Untuk medium, resize jika lebih dari 1024px
                            if img.size[0] > settings['office_image_max_size'][0] or img.size[1] > settings['office_image_max_size'][1]:
                                img.thumbnail(settings['office_image_max_size'], Image.Resampling.LANCZOS)
                                logger.info(f"Resized office image from {original_size} to {img.size} for medium compression")
                        else:  # large
                            # Untuk large, resize sesuai pengaturan
                            if img.size[0] > settings['office_image_max_size'][0] or img.size[1] > settings['office_image_max_size'][1]:
                                img.thumbnail(settings['office_image_max_size'], Image.Resampling.LANCZOS)
                                logger.info(f"Resized office image from {original_size} to {img.size} for large compression")
                    
                    # Save with compression based on level
                    ext = img_name.lower().split('.')[-1]
                    if ext in ['jpg', 'jpeg']:
                        if office_type == 'docx':
                            # Untuk Word, kompresi yang lebih efektif
                            if compression_level == 'small':
                                # Skala kecil = kualitas sedang (75)
                                img.save(img_path, 'JPEG', 
                                        quality=75, 
                                        optimize=True, 
                                        progressive=True,
                                        subsampling=1)
                            elif compression_level == 'medium':
                                # Skala sedang = kualitas rendah (65)
                                img.save(img_path, 'JPEG', 
                                        quality=65, 
                                        optimize=True, 
                                        progressive=True,
                                        subsampling=1)
                            else:  # large
                                # Skala besar = kualitas sangat rendah (50)
                                img.save(img_path, 'JPEG', 
                                        quality=50, 
                                        optimize=True, 
                                        progressive=True,
                                        subsampling=1)
                        else:
                            # Untuk file lain, gunakan logika normal
                            if compression_level == 'small':
                                # Untuk kompresi kecil, gunakan kualitas tinggi
                                img.save(img_path, 'JPEG', 
                                        quality=settings['office_image_quality'], 
                                        optimize=True, 
                                        progressive=True,
                                        subsampling=1)
                            else:
                                img.save(img_path, 'JPEG', quality=settings['office_image_quality'], optimize=True)
                    elif ext == 'png':
                        if office_type == 'docx':
                            # Untuk Word, kompresi yang lebih efektif
                            if compression_level == 'small':
                                # Skala kecil = kompresi sedang
                                img.save(img_path, 'PNG', 
                                        optimize=True, 
                                        compress_level=7,
                                        bits=8)
                            elif compression_level == 'medium':
                                # Skala sedang = kompresi agresif
                                img.save(img_path, 'PNG', 
                                        optimize=True, 
                                        compress_level=8,
                                        bits=8)
                            else:  # large
                                # Skala besar = kompresi maksimal
                                img.save(img_path, 'PNG', 
                                        optimize=True, 
                                        compress_level=9,
                                        bits=8)
                        else:
                            # Untuk file lain, gunakan logika normal
                            if compression_level == 'small':
                                # Untuk kompresi kecil, gunakan kompresi yang seimbang
                                img.save(img_path, 'PNG', 
                                        optimize=True, 
                                        compress_level=6,
                                        bits=8)
                            else:
                                img.save(img_path, 'PNG', optimize=True, compress_level=9)
                    else:
                        img.save(img_path, quality=settings['office_image_quality'], optimize=True)
                    
                    compressed_images += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to compress image {img_name}: {e}")
                    continue
        
        logger.info(f"Compressed {compressed_images} images in {office_type}")
        
        # Khusus untuk Excel, tambahkan kompresi tambahan
        if office_type == 'xlsx':
            # Kompresi tambahan untuk file Excel
            excel_compression_level = 9 if compression_level in ['medium', 'large'] else 6
            
            # Kompresi file XML dalam Excel
            xml_files = ['xl/workbook.xml', 'xl/worksheets/sheet*.xml', 'xl/styles.xml', 'xl/theme/theme*.xml']
            for xml_pattern in xml_files:
                import glob
                xml_files_found = glob.glob(os.path.join(temp_dir, xml_pattern))
                for xml_file in xml_files_found:
                    try:
                        # Baca dan kompresi XML
                        with open(xml_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Hapus whitespace yang tidak perlu untuk kompresi
                        if compression_level in ['medium', 'large']:
                            import re
                            # Hapus whitespace berlebih
                            content = re.sub(r'\s+', ' ', content)
                            content = re.sub(r'>\s+<', '><', content)
                            # Hapus komentar XML yang tidak perlu
                            content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
                            # Hapus baris kosong
                            content = re.sub(r'\n\s*\n', '\n', content)
                        
                        # Tulis kembali
                        with open(xml_file, 'w', encoding='utf-8') as f:
                            f.write(content)
                    except Exception as e:
                        logger.warning(f"Failed to compress XML {xml_file}: {e}")
            
            # Hapus file yang tidak perlu untuk kompresi
            if compression_level in ['medium', 'large']:
                unnecessary_files = [
                    'xl/printerSettings',
                    'xl/calcChain.xml',
                    'xl/queryTables',
                    'xl/externalLinks',
                    'xl/ctrlProps',
                    'xl/vbaProject.bin'
                ]
                
                for file_path in unnecessary_files:
                    full_path = os.path.join(temp_dir, file_path)
                    if os.path.exists(full_path):
                        if os.path.isfile(full_path):
                            os.remove(full_path)
                        elif os.path.isdir(full_path):
                            shutil.rmtree(full_path)
                        logger.info(f"Removed unnecessary Excel file: {file_path}")
        
        # Khusus untuk Word, tambahkan kompresi tambahan
        elif office_type == 'docx':
            # Kompresi tambahan untuk file Word - LEBIH EFEKTIF
            # Semua skala akan memberikan kompresi yang signifikan
            word_compression_level = 9  # Selalu gunakan kompresi maksimal
            
            # Kompresi file XML dalam Word - LEBIH AGRESIF
            xml_files = ['word/document.xml', 'word/styles.xml', 'word/settings.xml', 'word/fontTable.xml', 'word/theme/theme*.xml', 'word/numbering.xml', 'word/webSettings.xml']
            for xml_pattern in xml_files:
                import glob
                xml_files_found = glob.glob(os.path.join(temp_dir, xml_pattern))
                for xml_file in xml_files_found:
                    try:
                        # Baca dan kompresi XML
                        with open(xml_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Hapus whitespace yang tidak perlu untuk kompresi - LEBIH AGRESIF
                        import re
                        # Hapus whitespace berlebih
                        content = re.sub(r'\s+', ' ', content)
                        content = re.sub(r'>\s+<', '><', content)
                        # Hapus komentar XML yang tidak perlu
                        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
                        # Hapus baris kosong
                        content = re.sub(r'\n\s*\n', '\n', content)
                        # Hapus spasi di akhir tag
                        content = re.sub(r'\s+/>', '/>', content)
                        # Hapus spasi di awal dan akhir
                        content = content.strip()
                        
                        # Tulis kembali
                        with open(xml_file, 'w', encoding='utf-8') as f:
                            f.write(content)
                    except Exception as e:
                        logger.warning(f"Failed to compress XML {xml_file}: {e}")
            
            # Hapus file yang tidak perlu untuk kompresi Word - LEBIH AGRESIF
            # Hapus file pada semua skala untuk kompresi yang lebih efektif
            unnecessary_files = [
                'word/comments.xml',
                'word/endnotes.xml',
                'word/footnotes.xml',
                'word/glossary',
                'word/header*.xml',
                'word/footer*.xml',
                'word/vbaProject.bin',
                'word/embeddings',
                'word/activeX',
                'word/people.xml',
                'word/fontTable.xml',  # Hapus font table jika tidak ada font custom
                'word/settings.xml',   # Hapus settings yang tidak penting
                'word/webSettings.xml' # Hapus web settings
            ]
            
            for file_path in unnecessary_files:
                full_path = os.path.join(temp_dir, file_path)
                if os.path.exists(full_path):
                    if os.path.isfile(full_path):
                        os.remove(full_path)
                    elif os.path.isdir(full_path):
                        shutil.rmtree(full_path)
                    logger.info(f"Removed unnecessary Word file: {file_path}")
            
            # Hapus file header dan footer yang tidak digunakan
            header_footer_patterns = ['word/header*.xml', 'word/footer*.xml']
            for pattern in header_footer_patterns:
                import glob
                header_footer_files = glob.glob(os.path.join(temp_dir, pattern))
                for hf_file in header_footer_files:
                    try:
                        with open(hf_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        # Jika header/footer kosong atau hanya berisi whitespace, hapus file
                        if not content.strip() or len(content.strip()) < 100:
                            os.remove(hf_file)
                            logger.info(f"Removed empty header/footer: {hf_file}")
                    except Exception as e:
                        logger.warning(f"Failed to check header/footer {hf_file}: {e}")
            
            # Kompresi tambahan: hapus relasi yang tidak perlu
            rels_file = os.path.join(temp_dir, 'word', '_rels', 'document.xml.rels')
            if os.path.exists(rels_file):
                try:
                    with open(rels_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Hapus relasi yang tidak diperlukan
                    import re
                    # Hapus relasi ke file yang sudah dihapus
                    content = re.sub(r'<Relationship[^>]*Target="[^"]*(?:comments|endnotes|footnotes|glossary|header|footer|vbaProject|embeddings|activeX|people)[^"]*"[^>]*/>', '', content)
                    # Bersihkan whitespace
                    content = re.sub(r'\s+', ' ', content)
                    content = re.sub(r'>\s+<', '><', content)
                    
                    with open(rels_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                except Exception as e:
                    logger.warning(f"Failed to compress rels file: {e}")
        
        # Recreate the office file with appropriate compression - LEBIH EFEKTIF UNTUK WORD
        if office_type == 'docx':
            # Untuk Word, gunakan kompresi yang lebih agresif pada semua skala
            if compression_level == 'small':
                # Skala kecil = kompresi sedang (level 7)
                with zipfile.ZipFile(outpath.replace(f'.{office_type}', '') + '.zip', 'w', zipfile.ZIP_DEFLATED, compresslevel=7) as zipf:
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_dir)
                            zipf.write(file_path, arcname)
            elif compression_level == 'medium':
                # Skala sedang = kompresi agresif (level 8)
                with zipfile.ZipFile(outpath.replace(f'.{office_type}', '') + '.zip', 'w', zipfile.ZIP_DEFLATED, compresslevel=8) as zipf:
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_dir)
                            zipf.write(file_path, arcname)
            else:  # large
                # Skala besar = kompresi maksimal (level 9)
                with zipfile.ZipFile(outpath.replace(f'.{office_type}', '') + '.zip', 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_dir)
                            zipf.write(file_path, arcname)
        else:
            # Untuk file lain (Excel, PowerPoint), gunakan logika normal
            if compression_level == 'small':
                # Untuk kompresi kecil, gunakan kompresi ZIP yang seimbang
                with zipfile.ZipFile(outpath.replace(f'.{office_type}', '') + '.zip', 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_dir)
                            zipf.write(file_path, arcname)
            else:
                # Untuk medium dan large, gunakan kompresi ZIP yang lebih agresif
                compression_level_zip = 9 if compression_level == 'large' else 8
                with zipfile.ZipFile(outpath.replace(f'.{office_type}', '') + '.zip', 'w', zipfile.ZIP_DEFLATED, compresslevel=compression_level_zip) as zipf:
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, temp_dir)
                            zipf.write(file_path, arcname)
        
        shutil.rmtree(temp_dir)
        
        # Rename .zip to original extension
        zip_path = outpath.replace(f'.{office_type}', '') + '.zip'
        if os.path.exists(outpath):
            os.remove(outpath)
        os.rename(zip_path, outpath)
        
        logger.info(f"Office file compressed: {outpath}")
        return outpath
        
    except Exception as e:
        logger.error(f"Error compressing office file: {e}")
        # Fallback: copy original file
        outname = os.path.basename(filepath)
        outpath = os.path.join(outdir, outname)
        shutil.copy2(filepath, outpath)
        return outpath

@app.route('/', methods=['GET', 'POST'])
def index():
    stats = None
    preview_url = None
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Ambil level kompresi dari form
            compression_level = request.form.get('compression_level', 'medium')
            logger.info(f"Processing file: {filename} with compression level: {compression_level}")
            
            ext = filename.rsplit('.', 1)[1].lower()
            if ext in {'png', 'jpg', 'jpeg', 'gif', 'bmp'}:
                outpath = compress_image(filepath, app.config['RESULT_FOLDER'], compression_level)
                session['preview'] = filename
                preview_url = url_for('preview_image', filename=filename)
                out_filename = filename
            elif ext == 'pdf':
                outpath = compress_pdf_ghostscript(filepath, app.config['RESULT_FOLDER'], compression_level)
                out_filename = filename
            elif ext in {'docx', 'xlsx', 'pptx'}:
                outpath = compress_office_images(filepath, app.config['RESULT_FOLDER'], ext, compression_level)
                out_filename = filename
            else:
                outpath = os.path.join(app.config['RESULT_FOLDER'], filename)
                with open(filepath, 'rb') as src, open(outpath, 'wb') as dst:
                    dst.write(src.read())
                out_filename = filename
            
            # Statistik kompresi
            size_before = os.path.getsize(filepath)
            size_after = os.path.getsize(outpath)
            ratio = round(size_after / size_before * 100, 2) if size_before > 0 else 0
            
            logger.info(f"Compression stats - Before: {size_before}, After: {size_after}, Ratio: {ratio}%")
            
            stats = {
                'size_before': size_before,
                'size_after': size_after,
                'ratio': ratio,
                'compression_level': compression_level
            }
            session['stats'] = stats
            session['outpath'] = outpath
            session['filename'] = out_filename
            return redirect(url_for('result'))
        else:
            flash('File tidak didukung')
            return redirect(request.url)
    return render_template('index.html', stats=stats, preview_url=preview_url)

@app.route('/result')
def result():
    stats = session.get('stats')
    preview_url = None
    filename = session.get('preview')
    if filename:
        preview_url = url_for('preview_image', filename=filename)
    return render_template('result.html', stats=stats, preview_url=preview_url)

@app.route('/preview/<filename>')
def preview_image(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    with open(filepath, 'rb') as f:
        img_bytes = f.read()
    return send_file(io.BytesIO(img_bytes), mimetype='image/jpeg')

@app.route('/download')
def download():
    outpath = session.get('outpath')
    filename = session.get('filename')
    if outpath and filename:
        return send_file(outpath, as_attachment=True, download_name=filename)
    flash('File tidak ditemukan')
    return redirect(url_for('index'))

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True) 