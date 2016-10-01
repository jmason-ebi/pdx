from __future__ import unicode_literals

from django.db import models
from django_extensions.db.models import TimeStampedModel
from django.core import urlresolvers

NO = 0
YES = 1
UNKNOWN = 3
STATUS_CHOICES = (
    (YES, 'Yes'),
    (NO, 'No'),
    (UNKNOWN, 'Unknown'),
)


class DataSource(TimeStampedModel):
    name = models.CharField(max_length=200)
    description = models.TextField()

    def __unicode__(self):
        return self.name


class Response(TimeStampedModel):
    result = models.TextField()

    def __unicode__(self):
        return self.result


class Regime(TimeStampedModel):
    regime = models.TextField()


    def __unicode__(self):
        return self.regime

class Treatment(TimeStampedModel):
    drug = models.TextField()
    dose = models.TextField()

    regime = models.OneToOneField(Regime)
    response = models.OneToOneField(Response)


    def __unicode__(self):
        return self.drug, self.dose




class TumorHistology(TimeStampedModel):
    description = models.TextField()
    image = models.ImageField(upload_to="histology")

    class Meta:
        verbose_name_plural = "Tumor Histology Images"



class Patient(TimeStampedModel):
    external_id = models.CharField(max_length=10, blank=True)
    sex = models.CharField(max_length=10, blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    race = models.TextField(blank=True, null=True)
    ethnicity = models.TextField(blank=True, null=True)

    prior_treatment = models.ManyToManyField(Treatment)

    def __unicode__(self):
        return "".join([self.sex, ",", str(self.age)])


class PatientSnapshot(TimeStampedModel):
    patient = models.ForeignKey(Patient)
    age = models.IntegerField(blank=True, null=True)
    stage = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return "PatientSnapshot [Age: %s y.o., Sex: %s]"% (self.age, self.patient.sex)


class Tumor(TimeStampedModel):
    source_tumor_id = models.CharField(max_length=255, blank=True, null=True)
    tumor_type = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    diagnosis = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    tissue_of_origin = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    classification = models.CharField(max_length=100, blank=True, null=True)

    patient_snapshot = models.ForeignKey(PatientSnapshot, blank=True, null=True)
    histology = models.ForeignKey(TumorHistology, blank=True, null=True)

    def __unicode__(self):
        desc = "Tissue: %s (%s, Classification: %s)" % (self.tissue_of_origin, self.tumor_type, self.classification)
        if not self.patient_snapshot:
            desc = "Source specimen: Mouse %s" % "pdx"
        return desc

class ImplantationSite(TimeStampedModel):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name



class ImplantationType(TimeStampedModel):
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name



class HostStrain(TimeStampedModel):
    name = models.TextField()
    accession = models.TextField()
    humanized = models.TextField()
    humanization_protocol = models.TextField()

    def __unicode__(self):
        return "%s" % (self.name)


class PdxStrain(TimeStampedModel):
    external_id = models.CharField(max_length=100)
    passage_number = models.CharField(max_length=25, blank=True, null=True)
    lag_time = models.CharField(max_length=25, blank=True, null=True)
    doubling_time = models.CharField(max_length=25, blank=True, null=True)
    metastases = models.SmallIntegerField(null=True, blank=True, default=None, choices=STATUS_CHOICES)

    human_tumor = models.OneToOneField(Tumor, related_name='human_tumor')
    mouse_tumor = models.OneToOneField(Tumor, related_name='mouse_tumor')
    host_strain = models.ForeignKey(HostStrain)
    implantation_site = models.ForeignKey(ImplantationSite, blank=True, null=True)
    implantation_type = models.ForeignKey(ImplantationType, blank=True, null=True)
    data_source = models.ForeignKey(DataSource)
    treatment = models.ForeignKey(Treatment, blank=True, null=True)

    def __unicode__(self):
        return "Strain: %s (ID: %s), Implanted [Site:%s, Type: %s]"% (self.host_strain.name, self.external_id, self.implantation_site, self.implantation_type)

    def get_absolute_url(self):
        return urlresolvers.reverse('pdx', args=[self.pk])





class Validation(TimeStampedModel):
    status = models.CharField(max_length=100, blank=True, null=True)
    result = models.TextField()

    pdx_strain = models.ForeignKey(PdxStrain)

    def __unicode__(self):
        return self.result


class Marker(TimeStampedModel):
    gene = models.CharField(max_length=255, db_index=True)
    details = models.TextField(blank=True, null=True)

    tumor = models.ForeignKey(Tumor)

    def __unicode__(self):
        return "%s: %s" % (self.gene, self.details)

    def get_absolute_url(self):

        return urlresolvers.reverse('pdx', args=[self.tumor.mouse_tumor.pk])



