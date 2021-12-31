from django.core.management.base import BaseCommand
from django.db.models import Value, F, Func
from django.contrib.postgres.search import SearchVector

from services.models import ( 
    Service,
    ServiceNode,
    Unit,  
)

class Command(BaseCommand):
    help = "Re-indexes all entries, blogmarks, quotations"

    def handle(self, *args, **kwargs):
        print("Units", Unit.objects.update(vector_column=unit_vector_column))
        print("Services", Service.objects.update(vector_column=service_vector_column))
        print("ServiceNodes", ServiceNode.objects.update(vector_column=servicenode_vector_column))


unit_vector_column = (
    SearchVector("name_fi", config="finnish", weight="A") +
    SearchVector("name_sv", config="swedish", weight="A") +
    SearchVector("name_en", config="english", weight="A") +
    SearchVector("extra",  weight="B")
     +     
    SearchVector("description_fi", config="finnish", weight="C") +
    SearchVector("description_sv", config="swedish", weight="C") +
    SearchVector("description_en", config="english", weight="C") 
)


service_vector_column = (
    SearchVector("name_fi", config="finnish", weight="A") +
    SearchVector("name_sv", config="swedish", weight="A") +
    SearchVector("name_en", config="english", weight="A")    
)
servicenode_vector_column = (
    SearchVector("name_fi", config="finnish", weight="A") +
    SearchVector("name_sv", config="swedish", weight="A") +
    SearchVector("name_en", config="english", weight="A")    
)
          