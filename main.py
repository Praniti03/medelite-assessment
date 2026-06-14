from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import io

from cms_client import fetch_provider_info, fetch_claims_metrics, build_report_data
from pdf_generator import generate_pdf
from docx_generator import generate_docx

app = FastAPI(title="Medelite Facility Assessment Generator")

# This serves your index.html frontend
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    """Serve the main webpage"""
    return FileResponse("static/index.html")


# This defines what data the frontend sends to the backend
class ReportRequest(BaseModel):
    ccn: str
    name_override: str = ""
    emr: str = ""
    current_census: str = ""
    patient_type: str = ""
    previous_coverage: str = "No"
    previous_performance: str = ""
    medical_coverage: str = ""


@app.get("/api/lookup/{ccn}")
async def lookup_facility(ccn: str):
    """
    Step 1 endpoint — user types CCN and clicks Lookup
    Returns a JSON preview of the facility data
    so the frontend can show it before downloading
    """
    # Validate CCN format
    ccn = ccn.strip()
    if not ccn.isdigit() or len(ccn) != 6:
        raise HTTPException(
            status_code=400,
            detail="CCN must be a 6-digit number. Example: 686123"
        )

    try:
        provider = await fetch_provider_info(ccn)
        return {
            "provider_name": provider.get("provider_name"),
            "state": provider.get("state"),
            "address": provider.get("provider_address"),
            "city": provider.get("city_town"),
            "zip": provider.get("zip_code"),
            "beds": provider.get("number_of_certified_beds"),
            "overall_rating": provider.get("overall_rating"),
            "health_inspection_rating": provider.get("health_inspection_rating"),
            "staffing_rating": provider.get("staffing_rating"),
            "quality_measure_rating": provider.get("qm_rating"),
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"CMS API error: {str(e)}"
        )


@app.post("/api/generate-pdf")
async def generate_pdf_report(request: ReportRequest):
    """
    Step 2 endpoint — user fills manual fields and clicks Download PDF
    Fetches all CMS data, builds the PDF, streams it to the browser
    """
    try:
        # Fetch all data from CMS
        provider = await fetch_provider_info(request.ccn)
        claims = await fetch_claims_metrics(request.ccn)

        # Merge everything into one clean dictionary
        report_data = build_report_data(
            provider,
            claims,
            request.model_dump()
        )

        # Generate the PDF
        pdf_bytes = generate_pdf(report_data)

        # Stream it to the browser as a download
        filename = f"Facility_Assessment_{report_data['state']}_{request.ccn}.pdf"
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-docx")
async def generate_docx_report(request: ReportRequest):
    """
    Bonus endpoint — Download Word document
    """
    try:
        provider = await fetch_provider_info(request.ccn)
        claims = await fetch_claims_metrics(request.ccn)

        report_data = build_report_data(
            provider,
            claims,
            request.model_dump()
        )

        docx_bytes = generate_docx(report_data)

        filename = f"Facility_Assessment_{report_data['state']}_{request.ccn}.docx"
        return StreamingResponse(
            io.BytesIO(docx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))