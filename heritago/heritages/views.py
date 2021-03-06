from django.core.exceptions import ObjectDoesNotExist
from django.core.files.uploadedfile import UploadedFile
from django.conf import settings
from django.http import HttpResponse
from rest_framework import generics
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework import mixins
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth.models import User

from heritages.models import Heritage, Multimedia, Annotation
from heritages.search import search_heritages, search_annotations
from heritages.serializers import HeritageSerializer, MultimediaSerializer, AnnotationSerializer, UserSerializer, \
                                    AnnotationPaleSerializer
from heritages.permissions import IsOwner, IsNotAnonymous, IsSelf


class HeritagesListView(generics.ListCreateAPIView):
    queryset = Heritage.objects.all()
    serializer_class = HeritageSerializer

    def list(self, request, *args, **kwargs):
        keyword = self.request.query_params.get("keyword", None)
        if not keyword:
            return super().list(request, *args, **kwargs)

        result = Response(search_heritages(keyword)).data
        return Response(i["_source"] for i in result["hits"]["hits"])


class HeritageView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Heritage.objects.all()
    serializer_class = HeritageSerializer


class MultimediaListView(generics.ListCreateAPIView):
    serializer_class = MultimediaSerializer

    def get_queryset(self):
        try:
            heritage = Heritage.objects.get(pk=self.kwargs["heritage_id"])
        except ObjectDoesNotExist:
            raise NotFound()
        return heritage.multimedia

    def perform_create(self, serializer):
        heritage_id = self.kwargs["heritage_id"]
        try:
            heritage = Heritage.objects.get(pk=heritage_id)
        except ObjectDoesNotExist:
            raise NotFound()
        return serializer.save(heritage=heritage)


class MultimediaView(generics.RetrieveDestroyAPIView):
    queryset = Multimedia.objects.all()
    serializer_class = MultimediaSerializer


class MultimediaFileView(ViewSet):

    @staticmethod
    def get_file(request, multimedia_id):
        try:
            m = Multimedia.objects.get(pk=multimedia_id)
        except ObjectDoesNotExist:
            raise NotFound(multimedia_id)
        file = UploadedFile(m.file)
        return HttpResponse(file, content_type="image/png")


class AnnotationListView(generics.ListCreateAPIView):
    serializer_class = AnnotationSerializer

    def get_queryset(self):
        queryset = Annotation.objects.all()
        heritage_id = self.kwargs["heritage_id"]
        if heritage_id is not None:
            queryset = queryset.filter(target__target_id__contains=heritage_id)
            return queryset
        else:
            return NotFound()

    def get_serializer_context(self):
        return {"target_id": self.request.build_absolute_uri(),
                "heritage_id": self.kwargs["heritage_id"]}

    def list(self, request, *args, **kwargs):
        keyword = self.request.query_params.get("keyword", None)
        if not keyword:
            return super().list(request, *args, **kwargs)

        result = Response(search_annotations(keyword)).data
        return Response(i["_source"] for i in result["hits"]["hits"])


class AnnotationPaleListView(generics.ListCreateAPIView):
    serializer_class = AnnotationPaleSerializer

    def get_queryset(self):
        return Annotation.objects.all()

    def get_serializer_context(self):
        return {"target_id": self.request.build_absolute_uri()}

    def list(self, request, *args, **kwargs):
        keyword = self.request.query_params.get("keyword", None)
        if not keyword:
            return super().list(request, *args, **kwargs)

        result = Response(search_annotations(keyword)).data
        return Response(i["_source"] for i in result["hits"]["hits"])


class AnnotationView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Annotation.objects.all()
    serializer_class = AnnotationSerializer


class AnnotationPaleView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Annotation.objects.all()
    serializer_class = AnnotationPaleSerializer


class Users(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDetail(mixins.RetrieveModelMixin,
                 mixins.UpdateModelMixin,
                 viewsets.GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsSelf,)

    def get_me(self, request):
        return Response(self.serializer_class(request.user).data)
