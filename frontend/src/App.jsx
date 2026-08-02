import { useState, useEffect } from "react";
import { UploadCloud, CheckCircle2, AlertTriangle, XCircle, HelpCircle, RotateCcw } from "lucide-react";
import "./App.css";

// Map backend decision strings to an icon so results are scannable at a glance.
const DECISION_ICONS = {
    accept: CheckCircle2,
    manual_review: AlertTriangle,
    reject: XCircle,
    not_supported: HelpCircle,
};

function App() {

    const [file, setFile] = useState(null);
    const [category, setCategory] = useState("FRD");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [dropdownOpen, setDropdownOpen] = useState(false);
    const [supportedCategories, setSupportedCategories] = useState([]);
    const [isDragging, setIsDragging] = useState(false);

    // Ask the backend which categories currently have a reference template
    // loaded, so we can flag "Coming Soon" ones in the dropdown.
    useEffect(() => {
        fetch("http://127.0.0.1:8000/supported-categories")
            .then((res) => res.json())
            .then((data) => setSupportedCategories(data.supported_categories || []))
            .catch((err) => console.error("Could not load supported categories:", err));
    }, []);


    const documents = [
        ["BRD", "Business Requirements Document"],
        ["FRD", "Functional Requirements Document"],
        ["SRS", "Software Requirements Specification"],
        ["PRD", "Product Requirements Document"],
        ["HLD", "High-Level Design Document"],
        ["LLD", "Low-Level Design Document"],
        ["TDD", "Technical Design Document"],
        ["API", "API Documentation"],
        ["DBD", "Database Design Document"],
        ["UAT", "User Acceptance Testing Document"],
        ["STP", "Software Test Plan"],
        ["STD", "Software Test Documentation"],
        ["RTM", "Requirements Traceability Matrix"],
        ["UM", "User Manual"],
        ["IG", "Installation Guide"],
        ["DG", "Deployment Guide"],
        ["OG", "Operations Guide"],
        ["MG", "Maintenance Guide"],
        ["TG", "Training Guide"],
        ["SP", "System Proposal"],
        ["FSR", "Feasibility Study Report"],
        ["R&D", "Research and Development Document"],
        ["POC", "Proof of Concept Document"],
        ["Architecture", "System Architecture Document"],
        ["Security", "Security Assessment Document"],
        ["Release Notes", "Release Notes Document"],
        ["Change Log", "Change Log Document"],
        ["Meeting Minutes", "Meeting Minutes Document"],
        ["Project Plan", "Project Planning Document"],
        ["Other", "Other Project Documents"]
    ];


    const validateDocument = async (selectedFile) => {

        const fileToValidate = selectedFile || file;

        if (!fileToValidate) {
            alert("Please select a PDF or DOCX file");
            return;
        }

        const formData = new FormData();

        formData.append("category", category);
        formData.append("file", fileToValidate);

        try {

            setLoading(true);
            setResult(null);

            const response = await fetch(
                "http://127.0.0.1:8000/validate-document",
                {
                    method: "POST",
                    body: formData,
                }
            );

            const data = await response.json();
            setResult(data);

        } catch (error) {
            console.error(error);
            alert("Validation failed. Check backend terminal.");
        } finally {
            setLoading(false);
        }
    };

    const resetValidation = () => {
        setFile(null);
        setResult(null);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setIsDragging(false);
        const dropped = e.dataTransfer.files?.[0];
        if (!dropped) return;
        const validExt = /\.(pdf|docx)$/i.test(dropped.name);
        if (!validExt) {
            alert("Please drop a PDF or DOCX file");
            return;
        }
        setFile(dropped);
        validateDocument(dropped);
    };

    return (
        <div className="page">
            <div className="badge">
                ✦ Talent Trail AI Validator
            </div>
            <h1>
                TalentTrail Document <br />
                Validation System
            </h1>
            <p className="subtitle">
                Upload project documents and validate whether they match the selected category using AI.
            </p>
            <div className="card">
                <div className="card-header">
                    Upload Project Document
                </div>
                <div className="card-body">
                    <label className="label">
                        Select Document Category
                    </label>
                    {/* CUSTOM DROPDOWN */}
                    <div className="custom-dropdown">
                        <div
                            className="dropdown-selected"
                            onClick={() =>
                                setDropdownOpen(!dropdownOpen)
                            }
                        >
                            <span>
                                <span className="doc-code">
                                    {
                                        documents.find(
                                            d => d[0] === category
                                        )?.[0]
                                    }
                                </span>
                                {
                                    documents.find(
                                        d => d[0] === category
                                    )?.[1]
                                }
                            </span>
                            <span className="dropdown-arrow">
                                {dropdownOpen ? "▲" : "▼"}
                            </span>
                        </div>
                        {
                            dropdownOpen && (
                                <div className="dropdown-options">
                                    {
                                        documents.map((doc) => {
                                            const isReady = supportedCategories.includes(doc[0]);
                                            return (
                                                <div
                                                    key={doc[0]}
                                                    className={`dropdown-option ${isReady ? "" : "dropdown-option-disabled"}`}
                                                    onClick={() => {
                                                        setCategory(doc[0]);
                                                        setDropdownOpen(false);
                                                    }}
                                                >
                                                    <span className="doc-code">
                                                        {doc[0]}
                                                    </span>
                                                    <span className="dropdown-option-text">
                                                        {doc[1]}
                                                    </span>
                                                </div>
                                            );
                                        })
                                    }
                                </div>
                            )
                        }
                    </div>
                    <label
                        className={`upload-box ${isDragging ? "upload-box-dragging" : ""}`}
                        onDragOver={(e) => {
                            e.preventDefault();
                            setIsDragging(true);
                        }}
                        onDragLeave={() => setIsDragging(false)}
                        onDrop={handleDrop}
                    >
                        <div className="upload-icon">
                            <UploadCloud size={44} strokeWidth={1.5} />
                        </div>
                        <h2>
                            {isDragging ? "Drop your file here" : "Select PDF / DOCX File"}
                        </h2>
                        <p>
                            {
                                file
                                    ? file.name
                                    : "No file selected — click or drag a file here"
                            }
                        </p>
                        <input
                            type="file"
                            accept=".pdf,.docx"
                            onChange={(e) => {
                                const picked = e.target.files[0];
                                setFile(picked);
                                if (picked) {
                                    validateDocument(picked);
                                }
                                // allow re-selecting the same file to re-run
                                e.target.value = "";
                            }}
                            hidden
                        />
                    </label>
                    {
                        loading && (
                            <div className="validating">
                                <span className="spinner"></span>
                                <span>Validating...</span>
                            </div>
                        )
                    }
                    {
                        result && (
                            <div
                                className={
                                    `result ${result.decision?.toLowerCase()}`
                                }
                            >
                                <div className="result-heading">
                                    {
                                        (() => {
                                            const Icon = DECISION_ICONS[result.decision?.toLowerCase()] || HelpCircle;
                                            return <Icon size={28} />;
                                        })()
                                    }
                                    <h2>
                                        {result.decision}
                                    </h2>
                                </div>
                                <div className="result-grid">
                                    <p>
                                        <strong>
                                            Predicted:
                                        </strong>
                                        {" "}
                                        {result.predicted_category}
                                    </p>
                                    <p>
                                        <strong>
                                            Confidence:
                                        </strong>
                                        {" "}
                                        {result.confidence}%
                                    </p>
                                    {
                                        result.structure_score !== undefined && (
                                            <p>
                                                <strong>
                                                    Structure:
                                                </strong>
                                                {" "}
                                                {result.structure_score}%
                                            </p>
                                        )
                                    }
                                    {
                                        result.content_score !== undefined && (
                                            <p>
                                                <strong>
                                                    Content:
                                                </strong>
                                                {" "}
                                                {result.content_score}%
                                            </p>
                                        )
                                    }
                                </div>
                                <p>
                                    <strong>
                                        Reason:
                                    </strong>
                                    {" "}
                                    {result.reason}
                                </p>
                                {
                                    result.missing_sections?.length > 0 && (
                                        <p>
                                            <strong>
                                                Missing Sections:
                                            </strong>
                                            {" "}
                                            {
                                                result.missing_sections.join(", ")
                                            }
                                        </p>
                                    )
                                }
                                <button
                                    type="button"
                                    className="reset-button"
                                    onClick={resetValidation}
                                >
                                    <RotateCcw size={18} />
                                    Validate Another Document
                                </button>
                            </div>
                        )
                    }
                </div>
            </div>
        </div>

    );
}

export default App;