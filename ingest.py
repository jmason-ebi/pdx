import argparse
import os
import sys
from datetime import datetime


import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web.settings")
django.setup()

from web.models import *

DATA_FILE_PATH = '../pdx_data'

def import_jax(args):
    """
    Import PDX data from JAX
    """

    if args['download'] :
        from ingest_pipelines import jax
        jax.run()

    # Delete should cascade and delete all JAX associated objects
    DataSource.objects.filter(name="JAX").delete()

    jax = DataSource(name="JAX", description="The Jackson Laboratory")
    jax.created=datetime.now()
    jax.modified=datetime.now()
    jax.save()

    from lxml import html
    for filename in os.listdir("%s/JAX"%(DATA_FILE_PATH)):
        with open("%s/JAX/%s"%(DATA_FILE_PATH,filename), 'r') as f:
            tree = html.fromstring(f.read())

        pdx_info = dict()

        # PDX information (skip first row)
        for x in tree.xpath("""//td[@class="data1"][1]/table/tr""")[1:]:
            a = [y.text for y in x.findall("td")]
            pdx_info.update( dict(zip(map(lambda x: x and x.replace(":", "") or None, a[0::2]), a[1::2]) ) )

        # Patient information
        for x in tree.xpath("""//td[@class="data2"][1]/table/tr""")[:1]:
            a = [y.text for y in x.findall("td")]
            pdx_info.update( dict(zip(map(lambda x: x and x.replace(":", "") or None, a[0::2]), a[1::2]) ) )

        # Short circuit if not all the data is available
        if "Tumor Type" not in pdx_info:
            continue

        # Information gathered into map, now create the PDX

        if "Sex" in pdx_info:
            p = Patient()
            p.sex = pdx_info["Sex"]
            p.age = pdx_info["Age"]
            (race, ethnicity) = pdx_info["Race / Ethnicity"].split(" / ")
            p.race = race
            p.ethnicity = ethnicity
            p.save()

            ps = PatientSnapshot()
            ps.patient = p
            ps.age = p.age
            ps.save()

        if "Strain" in pdx_info and pdx_info["Strain"]:
            try:
                host_strain = HostStrain.objects.get(name__exact=pdx_info["Strain"])
            except HostStrain.DoesNotExist:
                host_strain = HostStrain()
                host_strain.name = pdx_info["Strain"]
                host_strain.save()

        else :
            print "No strain information for PDX", pdx_info

        if "Sample Type" in pdx_info:
            try:
                itype = ImplantationType.objects.get(name__exact=pdx_info["Sample Type"])
            except ImplantationType.DoesNotExist:
                itype = ImplantationType()
                itype.name = pdx_info["Sample Type"]
                itype.save()

        if "Implantation Site" in pdx_info:
            try:
                isite = ImplantationSite.objects.get(name__exact=pdx_info["Implantation Site"])
            except ImplantationSite.DoesNotExist:
                if pdx_info["Implantation Site"] :
                    isite = ImplantationSite()
                    isite.name = pdx_info["Implantation Site"]
                    isite.save()
                else :
                    isite = None

        ht = Tumor()
        ht.tumor_type = pdx_info["Tumor Type"]
        ht.diagnosis = pdx_info["Initial Diagnosis"]
        if "Final Diagnosis" in pdx_info and pdx_info["Final Diagnosis"]:
            ht.diagnosis = pdx_info["Final Diagnosis"]
        ht.tissue_of_origin = pdx_info["Primary Site"]
        (stage, grade) = pdx_info["Stage / Grade"].split(" / ")
        if grade:
            ht.classification = "Grade: %s" %grade
        ps.stage = stage
        ps.save()
        ht.patient_snapshot = ps
        ht.save()

        mt = Tumor()
        mt.source_tumor_id = "Not Specified"
        mt.save()

        pdx = PdxStrain()
        pdx.external_id = pdx_info["Model ID"]
        pdx.host_strain = host_strain
        pdx.data_source = jax
        pdx.human_tumor = ht
        pdx.mouse_tumor = mt
        pdx.implantation_type = itype
        pdx.implantation_site = isite
        pdx.save()


def import_proxe():
    """
    Import PDX data from PROXE
    """
    # Delete should cascade and delete all JAX associated objects
    DataSource.objects.filter(name="PROXE").delete()

    proxe = DataSource(name="PROXE", description="The Proxe Project")
    proxe.created=datetime.now()
    proxe.modified=datetime.now()
    proxe.save()

    # Process Proxe ingest pipeline
    import csv
    t = csv.reader(open("%s/PROXE/proxe.tsv"%DATA_FILE_PATH, 'rU'), dialect="excel-tab")
    header = t.next()
    all_data = [dict(zip(header, map(str, row))) for row in t] 

    for data in all_data:

        # Skip records without the tissue of origin
        if not data["Patient Tumor Tissue"]:
            continue

        # Skip records without the tissue of origin
        if "NA" == data["Patient Tumor Tissue"]:
            continue

        # Patient data
        p = Patient()
        p.sex = data["Sex"]
        p.age = data["Age"] and int(float(data["Age"])) or None # Truncate to year
        race_ethnicity = data["Race/Ethnicity"].split("/")
        if len(race_ethnicity) == 2:
            p.race = race_ethnicity[0]
            p.ethnicity = race_ethnicity[1]
        elif len(race_ethnicity) == 1:
            p.race = race_ethnicity[0]
        p.save()

        # Patient Snapshot
        ps = PatientSnapshot()
        ps.patient = p
        ps.age = p.age
        ps.stage = data["FAB Classification"] and "FAB Classification %s" % (data["FAB Classification"]) or None
        ps.save()

        # Human Tumor information
        ht = Tumor()
        ht.tumor_type = ""
        ht.diagnosis = data["Pathologic Diagnosis"]
        ht.tissue_of_origin = data["Patient Tumor Tissue"]
        ht.patient_snapshot = ps
        ht.save()

        # Human tumor markers
        marker_list = data["Patient Tumor Mutations Positive"].strip().split("|")
        if "" in marker_list :
            marker_list.remove("")

        detail_list = data["Patient Tumor Mutations Details"].strip().split("|")
        if len(marker_list) > 0:
            for i in xrange(len(marker_list)):
                m = Marker()
                m.tumor = ht
                m.gene = marker_list[i].strip()

                if len(detail_list) > i:
                    m.details = detail_list[i].strip()
                m.save()


        # Mouse Tumor information
        mt = Tumor()
        mt.save()

        # Mouse tumor markers
        marker_list = data["PDX Molecular Alterations Positive"].strip().split("|")
        if "" in marker_list :
            marker_list.remove("")

        detail_list = data["PDX Molecular Details"].strip().split("|")
        if len(marker_list) > 0:
            for i in xrange(len(marker_list)) :
                m = Marker()
                m.tumor = mt
                m.gene = marker_list[i].strip()

                if len(detail_list) > i:
                    m.details = detail_list[i].strip()
                m.save()

        # Mouse strain
        if data["Mouse Strain"]:
            try:
                host_strain = HostStrain.objects.get(name__exact=data["Mouse Strain"])
            except HostStrain.DoesNotExist:
                host_strain = HostStrain()
                host_strain.name = data["Mouse Strain"]
                host_strain.save()
        else :
            print "No strain information for PDX", data["PDX Name"]

        # Implantation type
        try:
            itype = ImplantationType.objects.get(name__exact=data["Engraftment Routes"])
        except ImplantationType.DoesNotExist:
            itype = ImplantationType()
            itype.name = data["Engraftment Routes"]
            itype.save()

        pdx = PdxStrain()
        pdx.external_id = data["PDX Name"]
        pdx.human_tumor = ht
        pdx.mouse_tumor = mt
        pdx.host_strain = host_strain
        pdx.data_source = proxe
        pdx.implantation_type = itype
        passage_number = data["PDX Passage Immunophenotyped"]
        lag_time = data["Days to Harvest P1"]
        pdx.save()

        # If there is validation of this PDX
        if len(data["Patient Tumor Mutations Positive"].strip().split("|")) > 0:

            # Add Validation object
            v = Validation()
            v.pdx_strain = pdx
            v.status = data["PDX HemoSeq"]

            mouse_markers = set([x.gene for x in mt.marker_set.all()])
            human_markers = set([x.gene for x in ht.marker_set.all()])
            same = len(mouse_markers.intersection(human_markers))
            percent = "N/A"
            if len(human_markers) > 0:
                percent = str(same/len(human_markers)) + "%"
            v.result = "%s PDX concordance in %s of %s genes (%s total markers)" % (percent, same, len(human_markers), len(ht.marker_set.all()))

            v.save()

        print "Saving pdx %s for tumor %s" % (pdx, ht)








def import_europdx():
    """
    Import PDX data from EuroPDX resource
    """
    # Delete should cascade and delete all JAX associated objects
    DataSource.objects.filter(name="EUROPDX").delete()

    europdx = DataSource(name="EUROPDX", description="The EuroPDX Project")
    europdx.created=datetime.now()
    europdx.modified=datetime.now()
    europdx.save()

    # Process Proxe ingest pipeline
    import csv
    t = csv.reader(open("%s/EUROPDX/data_clinical_patients.txt"%DATA_FILE_PATH, 'rU'), dialect="excel-tab")
    t.next()
    t.next()
    t.next()
    t.next()
    header = t.next()
    patient_data = [dict(zip(header, map(str, row))) for row in t] 
    patient_data = {x['PATIENT_ID']:x for x in patient_data}

    t = csv.reader(open("%s/EUROPDX/data_clinical_samples.txt"%DATA_FILE_PATH, 'rU'), dialect="excel-tab")
    t.next()
    t.next()
    t.next()
    t.next()
    header = t.next()
    tumor_data = [dict(zip(header, map(str, row))) for row in t] 

    all_data = []
    for x in tumor_data:
        patient_info = patient_data[x['PATIENT_ID']]
        data_row = x.copy()
        data_row.update(patient_info)
        all_data.append(data_row)
    print

    for data in all_data:


        # Patient data
        try:
            # Existing patient
            p = Patient.objects.get(name__exact=data["PATIENT_ID"])
        except:
            p = Patient()
            p.external_id = data["PATIENT_ID"]
            p.sex = data["GENDER"]
            p.age = data["AGE"] and int(float(data["AGE"])) or None # Truncate to year
            p.save()

        # Patient Snapshot
        ps = PatientSnapshot()
        ps.patient = p
        ps.age = data["AGE_AT_COLLECTION"] and int(float(data["AGE_AT_COLLECTION"])) or None # Truncate to year
        ps.save()

        # Human Tumor information
        ht = Tumor()
        ht.tumor_type = data["SAMPLE_ORIGIN"]
        ht.diagnosis = "Colorectal Adenocarcinoma"
        ht.tissue_of_origin = data["SITE_OF_PRIMARY"]
        ht.patient_snapshot = ps
        ht.classification = "Grade: %s"%data["GRADE"]
        ht.save()

        # Mouse Tumor information
        mt = Tumor()
        mt.source_tumor_id = data["LOCAL_MODEL_ID"]
        mt.save()

        # Mouse strain
        if data["STRAIN"]:
            try:
                host_strain = HostStrain.objects.get(name__exact=data["STRAIN"])
            except HostStrain.DoesNotExist:
                host_strain = HostStrain()
                host_strain.name = data["STRAIN"]
                host_strain.save()
        else :
            print "No strain information for PDX", data["PDX Name"]
            mt.delete()
            ht.delete()
            ps.delete()
            p.delete()

        # Implantation type
        try:
            itype = ImplantationType.objects.get(name__exact=data["IMPLANT_TYPE"])
        except ImplantationType.DoesNotExist:
            itype = ImplantationType()
            itype.name = data["IMPLANT_TYPE"]
            itype.save()

        try:
            isite = ImplantationSite.objects.get(name__exact=data["IMPLANT_SITE"])
        except ImplantationSite.DoesNotExist:
            isite = ImplantationSite()
            isite.name = data["IMPLANT_SITE"]
            isite.save()

        pdx = PdxStrain()
        pdx.external_id = data["SAMPLE_ID"]
        pdx.human_tumor = ht
        pdx.mouse_tumor = mt
        pdx.host_strain = host_strain
        pdx.data_source = europdx
        pdx.implantation_type = itype
        pdx.implantation_site = isite
        pdx.save()

        # Validations

        if "FINGERPRINT_AVAILABLE" in data:
            v = Validation()
            v.result = "Fingerprint data available: %s"%data["FINGERPRINT_AVAILABLE"]
            v.pdx_strain = pdx
            v.save()


        print "Saving pdx %s for tumor %s" % (pdx, ht)






def main(args) :

    for source in args['datasources'] :

        if 'jax' in source.lower() :

            # Process JAX ingest pipeline
            import_jax(args)







        if 'proxe' in source.lower() :

            # Process PROXE ingest pipeline
            import_proxe()










        if 'europdx' in source  .lower() :
            # Process EuroPDX ingest pipeline
            import_europdx()


if __name__ == "__main__" :


    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Optionally download data from external pipelines and insert / update the models in the PDX database')
    parser.add_argument('datasources', metavar='DATASOURCES', type=str, nargs='+', help='Process the data ingest pipeline(s) specified, i.e. jax, europdx')

#    parser = parser.add_mutually_exclusive_group(required=False)
    parser.add_argument('--download', dest='download', action='store_true')
    parser.add_argument('--no-download', dest='download', action='store_false')
    parser.set_defaults(download=False)
    args = vars(parser.parse_args())

    main(args)
