import os

TEMPLATE = """<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vishant Gandhi | {title}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    colors: {{
                        brand: {{
                            50: '#f0f9ff',
                            100: '#e0f2fe',
                            500: '#0ea5e9',
                            600: '#0284c7',
                            900: '#0c4a6e',
                        }}
                    }},
                    fontFamily: {{
                        sans: ['Inter', 'system-ui', 'sans-serif'],
                    }}
                }}
            }}
        }}
    </script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        body {{ font-family: 'Inter', sans-serif; }}
        .hero-pattern {{
            background-color: #ffffff;
            background-image: radial-gradient(#e5e7eb 1px, transparent 1px);
            background-size: 20px 20px;
        }}
    </style>
</head>
<body class="bg-slate-50 text-slate-800 flex flex-col min-h-screen">

    <!-- Navigation -->
    <nav class="fixed w-full bg-white/90 backdrop-blur-sm border-b border-slate-200 z-50">
        <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <a href="index.html" class="text-xl font-bold text-slate-900 tracking-tight">Gandhi.PhD</a>
                </div>
                <div class="hidden sm:flex sm:items-center sm:space-x-8">
                    <a href="index.html" class="text-sm font-medium text-slate-600 hover:text-brand-600 transition">Home</a>
                    <a href="publications.html" class="text-sm font-medium text-slate-600 hover:text-brand-600 transition">Publications</a>
                    <a href="curriculum-vitae.html" class="text-sm font-medium text-slate-600 hover:text-brand-600 transition">CV</a>
                    <a href="news.html" class="text-sm font-medium text-slate-600 hover:text-brand-600 transition">News</a>
                    <a href="contact-me.html" class="text-sm font-medium text-slate-600 hover:text-brand-600 transition">Contact Me</a>
                    <a href="http://localhost:8501" target="_blank" class="text-sm font-medium text-brand-600 hover:text-brand-700 transition flex items-center gap-2">
                        <i class="fa-solid fa-flask text-xs"></i> Research Tools
                    </a>
                </div>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="flex-grow pt-24 pb-12">
        {content}
    </main>

    <!-- Footer -->
    <footer class="bg-slate-900 text-slate-400 py-12 mt-auto">
        <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h2 class="text-white text-xl font-bold mb-4">Vishant Gandhi</h2>
            <div class="flex justify-center space-x-6 mb-6">
                <a href="https://linkedin.com/in/vishant-gandhi" target="_blank" class="hover:text-brand-500 transition text-2xl"><i class="fa-brands fa-linkedin"></i></a>
                <a href="https://scholar.google.com/" target="_blank" class="hover:text-brand-500 transition text-2xl"><i class="fa-solid fa-graduation-cap"></i></a>
                <a href="http://zenglerlab.com" target="_blank" class="hover:text-brand-500 transition text-2xl"><i class="fa-solid fa-flask"></i></a>
            </div>
            <p class="mb-2"><i class="fa-solid fa-envelope mr-2"></i> vishant@gandhi.phd | vigandhi@ucsd.edu</p>
            <p class="mb-8"><i class="fa-solid fa-location-dot mr-2"></i> 3147 Biomedical Sciences Way, La Jolla, CA 92093</p>
            <div class="pt-8 border-t border-slate-800 text-sm">
                <p>&copy; 2026 Vishant Gandhi. All rights reserved.</p>
                <p class="mt-2 text-slate-500">Built with modern web standards.</p>
            </div>
        </div>
    </footer>

</body>
</html>"""

pages = {
    "index.html": {
        "title": "Home",
        "content": """
        <!-- Hero Section -->
        <section class="hero-pattern pt-16 pb-20 sm:pt-20 sm:pb-24">
            <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                <img src="https://ui-avatars.com/api/?name=Vishant+Gandhi&background=0ea5e9&color=fff&size=128" alt="Vishant Gandhi" class="w-32 h-32 rounded-full mx-auto mb-8 shadow-lg ring-4 ring-white">
                <h1 class="text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight mb-4">
                    Vishant Gandhi
                </h1>
                <p class="text-xl text-brand-600 font-medium mb-2">Bioengineering PhD Student @ UC San Diego</p>
                <p class="text-lg text-slate-600 max-w-2xl mx-auto mb-8">
                    Working at the intersection of deep-tech research and commercialization. 
                    Developing microbiome therapeutics in the Zengler Lab while actively engaging in the biotech venture ecosystem.
                </p>
                <div class="flex justify-center space-x-4">
                    <a href="contact-me.html" class="bg-brand-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-brand-700 transition shadow-sm">
                        <i class="fa-regular fa-envelope mr-2"></i>Contact Me
                    </a>
                    <a href="publications.html" class="bg-white text-slate-700 border border-slate-300 px-6 py-3 rounded-lg font-medium hover:bg-slate-50 transition shadow-sm">
                        View Research
                    </a>
                </div>
                
                <div class="flex justify-center space-x-6 mt-12 text-slate-400">
                    <a href="https://linkedin.com/in/vishant-gandhi" target="_blank" class="hover:text-brand-600 transition" title="LinkedIn"><i class="fa-brands fa-linkedin text-2xl"></i></a>
                    <a href="https://scholar.google.com/" target="_blank" class="hover:text-brand-600 transition" title="Google Scholar"><i class="fa-solid fa-graduation-cap text-2xl"></i></a>
                    <a href="http://zenglerlab.com" target="_blank" class="hover:text-brand-600 transition" title="Zengler Lab"><i class="fa-solid fa-flask text-2xl"></i></a>
                </div>
            </div>
        </section>

        <!-- About / Dual Identity Section -->
        <section class="py-20 bg-white border-t border-b border-slate-200">
            <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="grid md:grid-cols-2 gap-12 items-center">
                    <div>
                        <h2 class="text-3xl font-bold text-slate-900 mb-6">Bridging Science & Strategy</h2>
                        <p class="text-slate-600 leading-relaxed mb-6">
                            I am a PhD student in the Department of Bioengineering at UC San Diego, working in Dr. Karsten Zengler's Lab. Prior to my doctoral studies, I served as a Post-baccalaureate IRTA Fellow at the National Institute on Aging (NIH), investigating mouse aging models under Dr. Rafael DeCabo. I hold a B.S. in Bioengineering from UC Riverside.
                        </p>
                        <p class="text-slate-600 leading-relaxed mb-6">
                            Outside of research and venture analysis, I enjoy Formula 1, pickleball, hiking San Diego’s trails, and engaging in science communication to inspire the next generation of researchers.
                        </p>
                    </div>
                    <div class="grid grid-cols-2 gap-4">
                        <div class="bg-slate-50 p-6 rounded-xl border border-slate-100 shadow-sm text-center">
                            <i class="fa-solid fa-flask text-3xl text-brand-500 mb-4"></i>
                            <h3 class="font-bold text-slate-900 mb-2">Researcher</h3>
                            <p class="text-sm text-slate-500">Zengler Lab, UCSD</p>
                        </div>
                        <div class="bg-slate-50 p-6 rounded-xl border border-slate-100 shadow-sm text-center">
                            <i class="fa-solid fa-chart-line text-3xl text-brand-500 mb-4"></i>
                            <h3 class="font-bold text-slate-900 mb-2">Venture Analyst</h3>
                            <p class="text-sm text-slate-500">Aquillius Ventures</p>
                        </div>
                        <div class="bg-slate-50 p-6 rounded-xl border border-slate-100 shadow-sm text-center">
                            <i class="fa-solid fa-handshake text-3xl text-brand-500 mb-4"></i>
                            <h3 class="font-bold text-slate-900 mb-2">Partnerships</h3>
                            <p class="text-sm text-slate-500">Nucleate San Diego</p>
                        </div>
                        <div class="bg-slate-50 p-6 rounded-xl border border-slate-100 shadow-sm text-center">
                            <i class="fa-solid fa-graduation-cap text-3xl text-brand-500 mb-4"></i>
                            <h3 class="font-bold text-slate-900 mb-2">Fellow</h3>
                            <p class="text-sm text-slate-500">Rady School</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Highlights Galleries Section -->
        <section class="py-20 bg-slate-50">
            <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="text-center mb-16">
                    <h2 class="text-3xl font-bold text-slate-900 mb-4">Photo Highlights</h2>
                    <p class="text-lg text-slate-600 max-w-2xl mx-auto">A glimpse into life inside and outside the lab.</p>
                </div>
                
                <div class="grid md:grid-cols-3 gap-8">
                    <!-- Gallery 1 -->
                    <div class="bg-white rounded-2xl overflow-hidden shadow-sm border border-slate-200">
                        <img src="https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=600&q=80" alt="San Diego" class="w-full h-48 object-cover">
                        <div class="p-6">
                            <h3 class="text-xl font-bold text-slate-900 mb-2">Life Highlights</h3>
                            <p class="text-slate-600 text-sm">Adventures in San Diego & Beyond</p>
                        </div>
                    </div>
                    
                    <!-- Gallery 2 -->
                    <div class="bg-white rounded-2xl overflow-hidden shadow-sm border border-slate-200">
                        <img src="https://images.unsplash.com/photo-1532094349884-543bc11b234d?auto=format&fit=crop&w=600&q=80" alt="Laboratory" class="w-full h-48 object-cover">
                        <div class="p-6">
                            <h3 class="text-xl font-bold text-slate-900 mb-2">Research Highlights</h3>
                            <p class="text-slate-600 text-sm">Capturing the dynamic nature of laboratory research</p>
                        </div>
                    </div>
                    
                    <!-- Gallery 3 -->
                    <div class="bg-white rounded-2xl overflow-hidden shadow-sm border border-slate-200">
                        <img src="https://images.unsplash.com/photo-1582213782179-e0d53f98f2ca?auto=format&fit=crop&w=600&q=80" alt="Team" class="w-full h-48 object-cover">
                        <div class="p-6">
                            <h3 class="text-xl font-bold text-slate-900 mb-2">Zengler Lab</h3>
                            <p class="text-slate-600 text-sm">The team behind the science.</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
        """
    },
    "publications.html": {
        "title": "Publications",
        "content": """
        <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
            <h1 class="text-4xl font-extrabold text-slate-900 mb-8 border-b pb-4">Publications</h1>
            <p class="text-slate-600 mb-8 text-lg">My research spans microbiome therapeutics, absolute quantification, and translational multi-omics.</p>
            
            <div class="space-y-6">
                <!-- Example Publication -->
                <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                    <h3 class="text-xl font-bold text-brand-600 mb-2">UroCom: A Model Synthetic Community for the Urinary Tract</h3>
                    <p class="text-slate-800 font-medium mb-2">Gandhi V, et al.</p>
                    <p class="text-slate-500 text-sm mb-4">In Preparation (2026)</p>
                    <p class="text-slate-600">Developing a physiologically relevant synthetic community to mimic the urinary tract microbiome. Utilizing the MIND technique and MetaRibo-Seq for high-resolution analysis of active protein translation.</p>
                </div>
                
                <div class="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                    <h3 class="text-xl font-bold text-brand-600 mb-2">Probiotics and Prebiotics to Prevent Respiratory Infections</h3>
                    <p class="text-slate-800 font-medium mb-2">Zengler Lab (ARPA-H PROTECT Project)</p>
                    <p class="text-slate-500 text-sm mb-4">Ongoing Research</p>
                    <p class="text-slate-600">Investigating targeted microbiome modulation to enhance immune resilience against respiratory pathogens.</p>
                </div>
            </div>
            
            <div class="mt-12 text-center">
                <a href="https://scholar.google.com/" target="_blank" class="inline-flex items-center text-brand-600 font-bold hover:text-brand-700">
                    <i class="fa-brands fa-google mr-2"></i> View Full List on Google Scholar
                </a>
            </div>
        </div>
        """
    },
    "curriculum-vitae.html": {
        "title": "Curriculum Vitae",
        "content": """
        <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
            <div class="flex justify-between items-center mb-8 border-b pb-4">
                <h1 class="text-4xl font-extrabold text-slate-900">Curriculum Vitae</h1>
                <a href="#" class="bg-slate-900 text-white px-4 py-2 rounded font-medium hover:bg-slate-800 transition shadow-sm text-sm">
                    <i class="fa-solid fa-download mr-2"></i> Download PDF
                </a>
            </div>
            
            <div class="mb-10">
                <h2 class="text-2xl font-bold text-brand-600 mb-4 border-b border-brand-100 pb-2">Education</h2>
                <div class="mb-4">
                    <div class="flex justify-between items-baseline mb-1">
                        <h3 class="font-bold text-slate-900 text-lg">Ph.D. in Bioengineering</h3>
                        <span class="text-slate-500 text-sm font-medium">Present</span>
                    </div>
                    <p class="text-slate-700">University of California, San Diego</p>
                    <p class="text-slate-500 text-sm">Zengler Lab</p>
                </div>
                <div>
                    <div class="flex justify-between items-baseline mb-1">
                        <h3 class="font-bold text-slate-900 text-lg">B.S. in Bioengineering</h3>
                        <span class="text-slate-500 text-sm font-medium">Graduated</span>
                    </div>
                    <p class="text-slate-700">University of California, Riverside</p>
                </div>
            </div>

            <div class="mb-10">
                <h2 class="text-2xl font-bold text-brand-600 mb-4 border-b border-brand-100 pb-2">Experience</h2>
                <div class="mb-6">
                    <div class="flex justify-between items-baseline mb-1">
                        <h3 class="font-bold text-slate-900 text-lg">Venture Analyst</h3>
                        <span class="text-slate-500 text-sm font-medium">Present</span>
                    </div>
                    <p class="text-slate-700 mb-2">Aquillius Ventures</p>
                    <ul class="list-disc list-inside text-slate-600 text-sm space-y-1">
                        <li>Evaluate early-stage technologies and life science investment opportunities.</li>
                    </ul>
                </div>
                <div class="mb-6">
                    <div class="flex justify-between items-baseline mb-1">
                        <h3 class="font-bold text-slate-900 text-lg">Assistant Director of Partnerships</h3>
                        <span class="text-slate-500 text-sm font-medium">Present</span>
                    </div>
                    <p class="text-slate-700 mb-2">Nucleate San Diego</p>
                    <ul class="list-disc list-inside text-slate-600 text-sm space-y-1">
                        <li>Bridge the gap between academia and industry.</li>
                    </ul>
                </div>
                <div class="mb-6">
                    <div class="flex justify-between items-baseline mb-1">
                        <h3 class="font-bold text-slate-900 text-lg">Post-baccalaureate IRTA Fellow</h3>
                        <span class="text-slate-500 text-sm font-medium">Prior to PhD</span>
                    </div>
                    <p class="text-slate-700 mb-2">National Institute on Aging (NIH)</p>
                    <ul class="list-disc list-inside text-slate-600 text-sm space-y-1">
                        <li>Experimental Gerontology Section under Dr. Rafael DeCabo.</li>
                        <li>Investigated mouse aging models.</li>
                    </ul>
                </div>
            </div>
        </div>
        """
    },
    "news.html": {
        "title": "News",
        "content": """
        <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
            <h1 class="text-4xl font-extrabold text-slate-900 mb-8 border-b pb-4">News & Updates</h1>
            
            <div class="space-y-8 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-300 before:to-transparent">
                
                <!-- Timeline Item -->
                <div class="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                    <!-- Icon -->
                    <div class="flex items-center justify-center w-10 h-10 rounded-full border border-white bg-slate-100 text-brand-500 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2">
                        <i class="fa-solid fa-newspaper text-sm"></i>
                    </div>
                    <!-- Card -->
                    <div class="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                        <div class="flex items-center justify-between mb-1">
                            <h3 class="font-bold text-slate-900">New Website Launched</h3>
                            <time class="text-xs font-medium text-brand-600">Sept 2026</time>
                        </div>
                        <p class="text-slate-600 text-sm">Transitioned to a fully custom, modern web stack to host private research tools and my public portfolio.</p>
                    </div>
                </div>

                <!-- Timeline Item -->
                <div class="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                    <div class="flex items-center justify-center w-10 h-10 rounded-full border border-white bg-slate-100 text-brand-500 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2">
                        <i class="fa-solid fa-flask text-sm"></i>
                    </div>
                    <div class="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
                        <div class="flex items-center justify-between mb-1">
                            <h3 class="font-bold text-slate-900">LitRev Tool Development</h3>
                            <time class="text-xs font-medium text-brand-600">Summer 2026</time>
                        </div>
                        <p class="text-slate-600 text-sm">Successfully built and deployed an automated Literature Review tool customized for the Zengler lab's multi-omics pipelines.</p>
                    </div>
                </div>
            </div>
        </div>
        """
    },
    "contact-me.html": {
        "title": "Contact Me",
        "content": """
        <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 mt-8">
            <h1 class="text-4xl font-extrabold text-slate-900 mb-8 border-b pb-4">Contact Me</h1>
            
            <div class="grid md:grid-cols-2 gap-12">
                <div>
                    <h2 class="text-2xl font-bold text-slate-900 mb-6">Get in Touch</h2>
                    <p class="text-slate-600 mb-8">Whether you want to discuss microbiome therapeutics, venture capital in biotech, or just talk Formula 1, feel free to reach out!</p>
                    
                    <div class="space-y-4">
                        <div class="flex items-start">
                            <div class="flex-shrink-0 w-10 h-10 bg-brand-50 text-brand-600 rounded-full flex items-center justify-center mt-1">
                                <i class="fa-solid fa-envelope"></i>
                            </div>
                            <div class="ml-4">
                                <p class="text-sm font-medium text-slate-900">Email</p>
                                <a href="mailto:vishant@gandhi.phd" class="text-brand-600 hover:underline block">vishant@gandhi.phd</a>
                                <a href="mailto:vigandhi@ucsd.edu" class="text-brand-600 hover:underline block">vigandhi@ucsd.edu</a>
                            </div>
                        </div>
                        
                        <div class="flex items-start">
                            <div class="flex-shrink-0 w-10 h-10 bg-brand-50 text-brand-600 rounded-full flex items-center justify-center mt-1">
                                <i class="fa-solid fa-location-dot"></i>
                            </div>
                            <div class="ml-4">
                                <p class="text-sm font-medium text-slate-900">Lab Address</p>
                                <p class="text-slate-600">3147 Biomedical Sciences Way<br>La Jolla, CA 92093</p>
                            </div>
                        </div>
                        
                        <div class="flex items-start">
                            <div class="flex-shrink-0 w-10 h-10 bg-brand-50 text-brand-600 rounded-full flex items-center justify-center mt-1">
                                <i class="fa-brands fa-linkedin"></i>
                            </div>
                            <div class="ml-4">
                                <p class="text-sm font-medium text-slate-900">LinkedIn</p>
                                <a href="https://linkedin.com/in/vishant-gandhi" target="_blank" class="text-brand-600 hover:underline">Connect on LinkedIn</a>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
                    <form class="space-y-4">
                        <div>
                            <label for="name" class="block text-sm font-medium text-slate-700 mb-1">Name</label>
                            <input type="text" id="name" class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none" placeholder="Your Name">
                        </div>
                        <div>
                            <label for="email" class="block text-sm font-medium text-slate-700 mb-1">Email</label>
                            <input type="email" id="email" class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none" placeholder="your@email.com">
                        </div>
                        <div>
                            <label for="message" class="block text-sm font-medium text-slate-700 mb-1">Message</label>
                            <textarea id="message" rows="4" class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none" placeholder="How can I help you?"></textarea>
                        </div>
                        <button type="button" class="w-full bg-brand-600 text-white font-medium py-3 rounded-lg hover:bg-brand-700 transition shadow-sm">
                            Send Message
                        </button>
                    </form>
                </div>
            </div>
        </div>
        """
    }
}

for filename, data in pages.items():
    filepath = os.path.join(os.getcwd(), filename)
    with open(filepath, 'w') as f:
        f.write(TEMPLATE.format(title=data["title"], content=data["content"]))

print("Generated site files successfully.")
