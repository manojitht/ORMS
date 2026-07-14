import csv

from django.http import HttpResponse


def csv_response(filename, header, rows):
    """Build a downloadable CSV HttpResponse from a header row and an
    iterable of row tuples. Shared by every app's CSV export views so each
    one only needs to gather its own queryset and map it to plain rows.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(header)
    writer.writerows(rows)
    return response
