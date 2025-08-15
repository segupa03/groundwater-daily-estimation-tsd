from setuptools import setup, find_packages
import os

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# Get package data files
def get_package_data():
    """Get all package data files."""
    package_data = {}
    
    # Add sample data files
    sample_data_path = "groundwater_estimation/data/sample_data"
    if os.path.exists(os.path.join("src", sample_data_path)):
        package_data["groundwater_estimation"] = [
            "data/sample_data/*",
            "data/sample_data/*.sqlite",
            "data/sample_data/*.csv",
            "data/sample_data/*.xlsx"
        ]
    
    # Add any other data files
    for root, dirs, files in os.walk("src/groundwater_estimation"):
        if files:
            # Convert to package path
            package_path = root.replace("src/", "")
            for file in files:
                if not file.endswith(('.py', '.pyc', '__pycache__')):
                    rel_path = os.path.join(package_path, file)
                    if "groundwater_estimation" not in package_data:
                        package_data["groundwater_estimation"] = []
                    package_data["groundwater_estimation"].append(rel_path)
    
    return package_data

# Get all Python packages
packages = find_packages(where="src")

setup(
    name="groundwater-daily-estimation-tsd",
    version="0.1.0",
    author="Sebastian Gutierrez Pacheco",
    author_email="sebastian.gutierrez-pacheco.1@ulaval.ca",
    description="A Python package for estimating daily groundwater levels using trend-seasonal-decomposition methodology",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/groundwater-daily-estimation-tsd",
    
    # Package discovery
    packages=packages,
    package_dir={"": "src"},
    
    # Python version requirements
    python_requires=">=3.8",
    
    # Dependencies
    install_requires=requirements,
    
    # Development dependencies
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.900",
        ],
        "test": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
        ],
        "docs": [
            "sphinx>=4.0",
            "sphinx-rtd-theme>=1.0",
        ],
    },
    
    # Package data
    include_package_data=True,
    package_data=get_package_data(),
    
    # Entry points (if you want to create command-line tools)
    entry_points={
        "console_scripts": [
            "groundwater-estimation=groundwater_estimation.cli:main",
        ],
    },
    
    # Classifiers
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Hydrology",
        "Topic :: Scientific/Engineering :: Environmental Science",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    
    # Keywords
    keywords=[
        "groundwater", "hydrology", "water-level", "estimation", 
        "trend-seasonal-decomposition", "TSD", "time-series", "analysis"
    ],
    
    # Project URLs
    project_urls={
        "Bug Reports": "https://github.com/yourusername/groundwater-daily-estimation-tsd/issues",
        "Source": "https://github.com/yourusername/groundwater-daily-estimation-tsd",
        "Documentation": "https://groundwater-daily-estimation-tsd.readthedocs.io/",
    },
    
    # Zip safe
    zip_safe=False,
) 