#!/usr/bin/env python3
"""Inventory a privately supplied art ZIP without extracting or redistributing it."""
from __future__ import annotations
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import struct
import zipfile

COLUMNS = ['zip_path', 'filename', 'source_pack', 'kind', 'excluded_reason', 'width', 'height', 'sha256', 'page', 'page_evidence', 'layer', 'layer_evidence', 'palette_variant', 'action_facing_status', 'frame_timing_status', 'guide_candidates', 'import_destination', 'license_status']
PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'

def audit(archive_path: Path, output: Path) -> dict:
    if not archive_path.is_file():
        raise FileNotFoundError(f'Archive unavailable: {archive_path}')
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    actual_png_count = 0
    metadata_count = 0
    png_hashes = set()
    with zipfile.ZipFile(archive_path) as archive:
        entries = [entry for entry in archive.infolist() if not entry.is_dir()]
        if len(entries) > 100000 or sum(entry.file_size for entry in entries) > 4 * 1024**3:
            raise ValueError('Archive exceeds safety limits (100,000 files / 4 GiB uncompressed). Review privately before changing limits.')
        guides = [entry.filename for entry in entries if PurePosixPath(entry.filename).suffix.lower() in ['.txt', '.md', '.pdf'] and not PurePosixPath(entry.filename).name.startswith('._') and '__MACOSX' not in PurePosixPath(entry.filename).parts]
        for entry in entries:
            path = PurePosixPath(entry.filename)
            if path.is_absolute() or '..' in path.parts or '\\' in entry.filename:
                raise ValueError(f'Unsafe archive member path: {entry.filename}')
            metadata = '__MACOSX' in path.parts or path.name.startswith('._') or path.name == '.DS_Store'
            if entry.file_size > 64 * 1024**2:
                raise ValueError(f'Member exceeds64MiB limit: {entry.filename}')
            row = dict.fromkeys(COLUMNS, '')
            row.update(zip_path=entry.filename, filename=path.name, source_pack='/'.join(path.parts[:-1]), kind='metadata' if metadata else 'other', excluded_reason='macOS/AppleDouble metadata' if metadata else '', license_status='not_verified', import_destination='Unassigned; requires reviewed source/page/frame mapping')
            if metadata:
                metadata_count += 1
                rows.append(row)
                continue
            contents = archive.read(entry)
            row['sha256'] = hashlib.sha256(contents).hexdigest()
            if path.suffix.lower() == '.png':
                if len(contents) < 33 or contents[:8] != PNG_SIGNATURE or contents[12:16] != b'IHDR' or struct.unpack('>I', contents[8:12])[0] != 13:
                    raise ValueError(f'Invalid PNG header: {entry.filename}')
                width, height = struct.unpack('>II', contents[16:24])
                if width == 0 or height == 0:
                    raise ValueError(f'Invalid PNG dimensions: {entry.filename}')
                row.update(kind='png', width=width, height=height, action_facing_status='unknown_until_manual_guide_and_image_review', frame_timing_status='unknown; header inspection does not establish animation frames')
                actual_png_count += 1
                png_hashes.add(row['sha256'])
                page = re.search(r'(?<![A-Za-z0-9])(p(?:ONE|BOW|POL)[A-Za-z0-9]*|p[1-4][A-C]?)(?![A-Za-z0-9])', path.stem, re.IGNORECASE)
                layer = re.search(r'(0bot|0bas|1out|2clo|3fac|4har|5hat|6tla|7tlb|8top)', path.stem, re.IGNORECASE)
                if page:
                    row.update(page=page.group(1), page_evidence='inferred filename token; verify guide')
                if layer:
                    row.update(layer=layer.group(1), layer_evidence='inferred filename token; verify actual layer pixels')
                row['palette_variant'] = 'unparsed; preserve exact filename and inspect naming guide'
            row['guide_candidates'] = ' | '.join(guide for guide in guides if PurePosixPath(guide).parent == path.parent)
            rows.append(row)
    with (output / 'asset-archive-inventory.csv').open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    report = {
        'status': 'metadata_audited_manual_review_required',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'archive_filename': archive_path.name,
        'archive_sha256': hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        'files': len(rows),
        'metadata_files_excluded': metadata_count,
        'actual_png_count': actual_png_count,
        'distinct_png_hashes': len(png_hashes),
        'count_definition': 'ZIP files with .png suffix and valid PNG signature/IHDR dimensions, excluding metadata. Equal hashes remain separate source-file entries.',
        'image_pixel_decoding': 'not_performed; header/ZIP integrity only',
        'guide_contents_reviewed': False,
        'animation_frames_verified': False,
        'license_verified': False,
        'redistributed_source_images': False,
        'next_steps': ['Inspect decoded images and timing/layer/naming guides privately.', 'Confirm frame rectangles, pivots and page-paired gear manually before filling animation-frame-map.json.', 'Obtain/review explicit redistribution terms; creator links alone are insufficient.', 'Register only reviewed derived assets and verify them in the installed Unreal/PaperZD environment.'],
    }
    (output / 'archive-audit-report.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return report

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    try:
        report = audit(arguments.archive, arguments.output)
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError) as exception:
        parser.exit(1, f'Audit failed: {exception}\n')
    print(f"Audited {report['files']} files; {report['actual_png_count']} PNG headers; manual frame/license review required.")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
