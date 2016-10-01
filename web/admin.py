from django.contrib import admin
from web.models import *

# class TumorInline(admin.TabularInline):
# 	model = Tumor

# class PdxStrainInline(admin.TabularInline):
# 	model = PdxStrain
# 	extra = 8
# 	max_num = 10

# class DataSourceAdmin(admin.ModelAdmin):
# 	extra = 8
# 	max_num = 10
# 	inlines = [
# 		PdxStrainInline,
# 	]


# class TumorAdmin(admin.ModelAdmin):
# 	list_display = ['id', 'tumor_type', 'tissue_of_origin', 'classification']


class ValidationInline(admin.TabularInline):
	model = Validation


class MarkerInline(admin.TabularInline):
	model = Marker

class TumorInline(admin.TabularInline):
	model = Tumor
	readonly_fields=('id',)


class PatientSnapshotAdmin(admin.ModelAdmin):
	list_display = ['id', 'age', 'get_data_source', 'get_patient_sex']

	inlines = [
		TumorInline
	]

	def get_data_source(self, obj):
		return obj.tumor_set.first().human_tumor.data_source

	def get_patient_sex(self, obj):
		return obj.patient.sex


class PdxStrainInline(admin.TabularInline):
	model = PdxStrain

class PdxStrainAdmin(admin.ModelAdmin):
	list_display = ['id', 'implantation_type', 'implantation_site', 'data_source']
	inlines = [
		ValidationInline
	]


admin.site.register(Validation)
admin.site.register(Response)
admin.site.register(Regime)
admin.site.register(Treatment)
admin.site.register(HostStrain)
admin.site.register(ImplantationType)
admin.site.register(ImplantationSite)
admin.site.register(DataSource)
admin.site.register(PdxStrain, PdxStrainAdmin)
admin.site.register(TumorHistology)
admin.site.register(Patient)
admin.site.register(PatientSnapshot, PatientSnapshotAdmin)
admin.site.register(Tumor)
admin.site.register(Marker)
