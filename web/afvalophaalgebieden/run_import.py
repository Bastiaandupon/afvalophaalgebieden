import argparse
import os

import shapefile
from shapely.geometry import Polygon, Point
from geoalchemy2.shape import from_shape

from app import app
from app import models


class ImportBase(object):
    path = 'shp'
    file = None
    fieldnames = list()

    def __init__(self):
        self.fieldnames = list()

    def process_record(self, record):
        raise NotImplementedError

    def wrap_record(self, record):
        return dict(zip(self.fieldnames, record))

    def run(self):
        print('processing: %s' % self.file)
        filename = self.resolve_file(self.file)
        sf = shapefile.Reader(filename)

        [self.fieldnames.append(properties[0]) for properties in sf.fields if isinstance(properties, list)]

        shape_recs = sf.shapeRecords()
        [self.process_record(rec) for rec in shape_recs]

    def resolve_file(self, code):
        matches = [os.path.join(self.path, f) for f in os.listdir(self.path) if code in f.lower()]
        if not matches:
            raise ValueError("Could not find file for %s in %s" % (code, self.path))
        matches_with_mtime = [(os.path.getmtime(f), f) for f in matches]
        match = sorted(matches_with_mtime)[-1]
        return match[1]


class ImportHuisvuil(ImportBase):
    file = 'huisvuil'

    def process_record(self, record):
        fields = self.wrap_record(record.record)

        polygon = Polygon([tuple(p) for p in record.shape.points])
        wkb_element = from_shape(polygon, srid=28992)

        try:
            model = models.Huisvuil(
                type=fields['type'].strip(),
                ophaaldag=fields['ophaaldag'].strip(),
                aanbiedwij=fields['aanbiedwij'].strip(),
                opmerking=fields['opmerking'].strip(),
                tijd_vanaf=fields['tijd_vanaf'].strip(),
                tijd_tot=fields['tijd_tot'].strip(),
                mutatie=fields['mutatie'].strip(),
                sdid=fields['sdid'],
                sdnaam=fields['sdnaam'].strip(),
                sdcode=fields['sdcode'].strip(),
                geometrie=wkb_element
            )
            models.db.session.add(model)
            models.db.session.commit()
        except (KeyError, AttributeError):
            import ipdb;ipdb.set_trace()


class ImportGrofvuil(ImportBase):
    file = 'grofvuil'

    def process_record(self, record):
        fields = self.wrap_record(record.record)

        polygon = Polygon([tuple(p) for p in record.shape.points])
        wkb_element = from_shape(polygon, srid=28992)

        try:
            model = models.Grofvuil(
                ophaaldag=fields['ophaaldag'].strip(),
                buurtid='%r'.strip() % fields['buurtid'],
                naam=fields['naam'].strip(),
                vollcode=fields['vollcode'].strip(),
                opmerking=fields['opmerking'].strip(),
                website=fields['website'].strip(),
                tijd_vanaf=fields['tijd_vanaf'].strip(),
                tijd_tot=fields['tijd_tot'].strip(),
                type=fields['type'].strip(),
                mutatie=fields['mutatie'].strip(),
                sdid=fields['sdid'],
                sdnaam=fields['sdnaam'].strip(),
                sdcode=fields['sdcode'].strip(),
                geometrie=wkb_element
            )
            models.db.session.add(model)
            models.db.session.commit()
        except (KeyError, AttributeError):
            import ipdb;ipdb.set_trace()


class ImportKleinChemisch(ImportBase):
    file = 'kca'

    def process_record(self, record):
        fields = self.wrap_record(record.record)

        point = Point(record.shape.points[0])
        wkb_element = from_shape(point, srid=28992)

        try:
            model = models.KleinChemisch(
                type=fields['type'].strip(),
                tijd_van=fields['tijd_van'].strip(),
                tijd_tot=fields['tijd_tot'].strip(),
                dag=fields['dag'].strip(),
                mutatie=fields['mutatie'].strip(),
                sdid=fields['sdid'],
                sdnaam=fields['sdnaam'].strip(),
                sdcode=fields['sdcode'].strip(),
                geometrie=wkb_element
            )
            models.db.session.add(model)
            models.db.session.commit()
        except (KeyError, AttributeError):
            import ipdb;ipdb.set_trace()


if __name__ == '__main__':
    huisvuil_import = ImportHuisvuil()
    huisvuil_import.run()

    grofvuil_import = ImportGrofvuil()
    grofvuil_import.run()

    kca_import = ImportKleinChemisch()
    kca_import.run()