(() => {
  "use strict";
  const SAVED_KEY = "premier_saved_cars_v1";
  const money = value => new Intl.NumberFormat("en-US",{style:"currency",currency:"USD",maximumFractionDigits:0}).format(value);
  const cars = [
    {id:"bmw-330i-m-sport",make:"BMW",model:"3 Series",name:"BMW 330i M Sport",year:2024,price:58900,mileage:12400,transmission:"Automatic",fuel:"Petrol",condition:"used",body:"Sedan",engine:"2.0L Turbo",drive:"Rear-wheel drive",colour:"Portimao Blue",tag:"Just arrived",description:"A beautifully balanced sports sedan with confident performance, a driver-focused cabin and the unmistakable character of the BMW 3 Series. This example pairs everyday refinement with the sharper M Sport finish.",features:["M Sport package","Leather upholstery","Panoramic roof","Parking sensors","Apple CarPlay","Adaptive cruise control"],images:["https://images.unsplash.com/photo-1555215695-3004980ad54e?auto=format&fit=crop&w=1400&q=88","https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=1000&q=85","https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=1000&q=85"]},
    {id:"mercedes-c300",make:"Mercedes-Benz",model:"C-Class",name:"Mercedes-Benz C 300",year:2025,price:64900,mileage:0,transmission:"Automatic",fuel:"Petrol",condition:"new",body:"Sedan",engine:"2.0L Turbo",drive:"Rear-wheel drive",colour:"Obsidian Black",tag:"New arrival",description:"Modern luxury with a calm, considered interior and responsive turbocharged performance. The C 300 brings together elegant proportions, intuitive technology and the comfort expected from Mercedes-Benz.",features:["MBUX infotainment","Digital instrument display","Heated front seats","Driver assistance","LED lighting","Premium sound system"],images:["https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?auto=format&fit=crop&w=1400&q=88","https://images.unsplash.com/photo-1618843479618-39b5f6f5b2f0?auto=format&fit=crop&w=1000&q=85","https://images.unsplash.com/photo-1618843479313-40f8afb4b4d8?auto=format&fit=crop&w=1000&q=75"]},
    {id:"audi-q5-premium",make:"Audi",model:"Q5",name:"Audi Q5 Premium Plus",year:2024,price:52750,mileage:8200,transmission:"Automatic",fuel:"Petrol",condition:"used",body:"SUV",engine:"2.0L TFSI",drive:"Quattro all-wheel drive",colour:"Daytona Grey",tag:"Certified",description:"A versatile premium SUV with composed road manners, a beautifully finished cabin and the reassuring grip of quattro all-wheel drive. A strong choice for daily journeys and longer weekends away.",features:["Quattro AWD","Virtual cockpit","Panoramic sunroof","Leather seats","360° camera","Power tailgate"],images:["https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?auto=format&fit=crop&w=1400&q=88","https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?auto=format&fit=crop&w=1000&q=85","https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?auto=format&fit=crop&w=1000&q=75"]}
  ];
  const readSaved = () => { try { const value=JSON.parse(localStorage.getItem(SAVED_KEY)||"[]"); return Array.isArray(value)?value.filter(id=>cars.some(car=>car.id===id)):[]; } catch (_) { return []; } };
  const writeSaved = ids => { localStorage.setItem(SAVED_KEY,JSON.stringify([...new Set(ids)])); updateSavedCounts(); };
  function updateSavedCounts(){ const count=readSaved().length; document.querySelectorAll("[data-saved-count]").forEach(el=>el.textContent=count); }
  function cardMarkup(car){
    const saved=readSaved().includes(car.id);
    return `<article class="car-card" data-car-id="${car.id}">
      <div class="car-image"><a href="car.html?id=${encodeURIComponent(car.id)}" aria-label="View ${car.name}"><img src="${car.images[0]}" alt="${car.year} ${car.name}" loading="lazy" decoding="async"></a>
        <span class="car-tag">${car.tag}</span><button class="favorite ${saved?"is-saved":""}" type="button" data-save-car="${car.id}" aria-pressed="${saved}" aria-label="${saved?"Remove":"Save"} ${car.name}">${saved?"♥":"♡"}</button></div>
      <div class="car-info"><p class="car-kicker">${car.year} · ${car.condition==="new"?"Brand new":"Pre-owned"} · ${car.body}</p>
        <h3><a href="car.html?id=${encodeURIComponent(car.id)}">${car.name}</a></h3>
        <p class="car-meta"><span>${car.mileage?car.mileage.toLocaleString()+" mi":"New"}</span><span>${car.transmission}</span><span>${car.fuel}</span></p>
        <div class="car-bottom"><strong class="car-price">${money(car.price)}</strong><a class="car-open" href="car.html?id=${encodeURIComponent(car.id)}">View details <span aria-hidden="true">→</span></a></div></div>
    </article>`;
  }
  function populateFilters(){
    const make=document.getElementById("make-filter"),model=document.getElementById("model-filter"),year=document.getElementById("year-filter");
    if(!make||!model||!year)return;
    const options=(values,label)=>values.sort().map(value=>`<option value="${value}">${value}</option>`).join("");
    make.insertAdjacentHTML("beforeend",options([...new Set(cars.map(car=>car.make))]));
    model.insertAdjacentHTML("beforeend",options([...new Set(cars.map(car=>car.model))]));
    year.insertAdjacentHTML("beforeend",options([...new Set(cars.map(car=>String(car.year)))]));
  }
  let selectedCondition="all", selectedBrand="";
  function filteredCars(){
    const value=id=>document.getElementById(id)?.value||"";
    const keyword=value("keyword-filter").trim().toLowerCase(),make=value("make-filter"),model=value("model-filter"),year=value("year-filter"),price=Number(value("price-filter"))||Infinity,mileage=Number(value("mileage-filter"))||Infinity,transmission=value("transmission-filter"),fuel=value("fuel-filter"),condition=value("condition-filter"),body=value("body-filter");
    return cars.filter(car=>{
      const text=[car.name,car.make,car.model,car.year,car.body,car.fuel,car.description].join(" ").toLowerCase();
      return (!keyword||text.includes(keyword))&&(!make||car.make===make)&&(!model||car.model===model)&&(!year||String(car.year)===year)&&car.price<=price&&(!mileage||car.mileage<=mileage)&&(!transmission||car.transmission===transmission)&&(!fuel||car.fuel===fuel)&&(!condition||car.condition===condition)&&(!body||car.body===body)&&(!selectedCondition||selectedCondition==="all"||car.condition===selectedCondition)&&(!selectedBrand||car.make===selectedBrand);
    });
  }
  function renderInventory(){
    const grid=document.getElementById("inventory-grid");if(!grid)return;
    const result=filteredCars();grid.innerHTML=result.map(cardMarkup).join("");
    const count=document.getElementById("result-count");if(count)count.textContent=`${result.length} ${result.length===1?"vehicle":"vehicles"}`;
    const empty=document.getElementById("no-results");if(empty)empty.hidden=result.length!==0;
  }
  function renderSavedPage(){
    const grid=document.getElementById("saved-grid");if(!grid)return;
    const saved=readSaved().map(id=>cars.find(car=>car.id===id)).filter(Boolean);
    grid.innerHTML=saved.map(cardMarkup).join("");
    const empty=document.getElementById("saved-empty");if(empty)empty.hidden=saved.length>0;
  }
  function renderDetail(){
    const root=document.getElementById("car-detail-content");if(!root)return;
    const id=new URLSearchParams(location.search).get("id"),car=cars.find(item=>item.id===id);
    if(!car){root.innerHTML='<section class="saved-empty"><div class="empty-heart">⌕</div><h2>Vehicle not found.</h2><p>This vehicle may no longer be in the collection.</p><a class="button button-gold" href="index.html#inventory">Return to the collection →</a></section>';return;}
    document.title=car.name+" | Premier Motorworks";
    const saved=readSaved().includes(car.id);
    root.innerHTML=`<div class="detail-gallery">
      <div class="detail-main-image"><img id="detail-main-image" src="${car.images[0]}" alt="${car.name}" fetchpriority="high"></div>
      ${car.images.slice(0,3).map((src,index)=>`<button class="detail-thumb ${index===0?"is-active":""}" type="button" data-gallery-src="${src}" aria-label="Show vehicle image ${index+1}"><img src="${src}" alt="" loading="lazy" decoding="async"></button>`).join("")}
    </div><section class="detail-info"><p class="eyebrow">${car.year} · ${car.condition==="new"?"Brand new":"Pre-owned"} · ${car.body}</p><h1>${car.name}</h1><p class="detail-price">${money(car.price)}</p><p class="detail-description">${car.description}</p>
      <div class="detail-specs">
        <div class="spec-item"><span>Year</span><strong>${car.year}</strong></div><div class="spec-item"><span>Mileage</span><strong>${car.mileage?car.mileage.toLocaleString()+" mi":"Brand new"}</strong></div>
        <div class="spec-item"><span>Transmission</span><strong>${car.transmission}</strong></div><div class="spec-item"><span>Fuel type</span><strong>${car.fuel}</strong></div>
        <div class="spec-item"><span>Body type</span><strong>${car.body}</strong></div><div class="spec-item"><span>Engine</span><strong>${car.engine}</strong></div>
        <div class="spec-item"><span>Drivetrain</span><strong>${car.drive}</strong></div><div class="spec-item"><span>Exterior</span><strong>${car.colour}</strong></div>
      </div>
      <h2 class="detail-subhead">Features & equipment</h2><div class="feature-list">${car.features.map(item=>`<span>${item}</span>`).join("")}</div>
      <div class="seller-panel"><strong>Premier Motorworks</strong><p>Vehicle enquiries are handled by our sales team. Ask us about availability, viewing arrangements and the next steps.</p></div>
      <div class="detail-actions"><button class="button button-gold" type="button" data-whatsapp-enquiry="${car.id}">Enquire on WhatsApp ↗</button><button class="button button-outline" type="button" data-save-car="${car.id}" aria-pressed="${saved}">${saved?"♥ Saved":"♡ Save for later"}</button></div>
      <form class="detail-enquiry" id="detail-enquiry"><h2>Ask about this vehicle</h2><p>Prepare an enquiry message to send to the seller through WhatsApp.</p><div class="enquiry-form"><input name="name" autocomplete="name" placeholder="Your name" required><input name="phone" type="tel" autocomplete="tel" placeholder="Your phone number (optional)"><textarea name="message" placeholder="What would you like to know?"></textarea><button class="button button-gold" type="submit">Prepare enquiry ↗</button></div></form>
    </section>`;
  }
  function sendEnquiry(car,form){
    let name="",phone="",message="";
    if(form){const data=new FormData(form);name=String(data.get("name")||"").trim();phone=String(data.get("phone")||"").trim();message=String(data.get("message")||"").trim();}
    const body=[`Hello Premier Motorworks, I'm interested in the ${car.year} ${car.name} (${money(car.price)}).`,name?`Name: ${name}`:"",phone?`Phone: ${phone}`:"",message?`Message: ${message}`:"Please share availability and viewing details."].filter(Boolean).join("\\n");
    window.open("https://wa.me/?text="+encodeURIComponent(body),"_blank","noopener,noreferrer");
  }
  document.addEventListener("DOMContentLoaded",()=>{
    updateSavedCounts();populateFilters();renderInventory();renderSavedPage();renderDetail();
    const year=document.getElementById("current-year");if(year)year.textContent=new Date().getFullYear();
    const menu=document.querySelector(".menu-toggle"),nav=document.getElementById("main-nav");
    if(menu&&nav)menu.addEventListener("click",()=>{const open=nav.classList.toggle("is-open");menu.setAttribute("aria-expanded",String(open));menu.setAttribute("aria-label",open?"Close menu":"Open menu");});
    if(nav)nav.addEventListener("click",event=>{if(event.target.closest("a")){nav.classList.remove("is-open");menu?.setAttribute("aria-expanded","false");}});
    const search=document.getElementById("vehicle-search");
    if(search){search.addEventListener("submit",event=>{event.preventDefault();selectedBrand="";document.querySelectorAll("[data-brand]").forEach(button=>button.classList.remove("is-active"));renderInventory();document.getElementById("inventory")?.scrollIntoView({behavior:"smooth"});});search.addEventListener("input",renderInventory);search.addEventListener("change",renderInventory);search.addEventListener("reset",()=>{selectedCondition="all";selectedBrand="";document.querySelectorAll("[data-condition]").forEach(button=>button.classList.toggle("is-active",button.dataset.condition==="all"));document.querySelectorAll("[data-brand]").forEach(button=>button.classList.remove("is-active"));requestAnimationFrame(renderInventory);});}
    document.querySelectorAll("[data-condition]").forEach(button=>button.addEventListener("click",()=>{selectedCondition=button.dataset.condition;document.querySelectorAll("[data-condition]").forEach(item=>item.classList.toggle("is-active",item===button));renderInventory();}));
    document.querySelectorAll("[data-brand]").forEach(button=>button.addEventListener("click",()=>{selectedBrand=selectedBrand===button.dataset.brand?"":button.dataset.brand;document.querySelectorAll("[data-brand]").forEach(item=>item.classList.toggle("is-active",item.dataset.brand===selectedBrand));selectedCondition="all";document.querySelectorAll("[data-condition]").forEach(item=>item.classList.toggle("is-active",item.dataset.condition==="all"));renderInventory();document.getElementById("inventory")?.scrollIntoView({behavior:"smooth"});}));
    document.addEventListener("click",event=>{
      const save=event.target.closest("[data-save-car]");if(save){const id=save.dataset.saveCar,ids=readSaved(),next=ids.includes(id)?ids.filter(item=>item!==id):ids.concat(id);writeSaved(next);renderInventory();renderSavedPage();if(document.getElementById("car-detail-content"))renderDetail();return;}
      const thumb=event.target.closest("[data-gallery-src]");if(thumb){const main=document.getElementById("detail-main-image");if(main){main.src=thumb.dataset.gallerySrc;document.querySelectorAll("[data-gallery-src]").forEach(item=>item.classList.toggle("is-active",item===thumb));}return;}
      const enquiry=event.target.closest("[data-whatsapp-enquiry]");if(enquiry){const car=cars.find(item=>item.id===enquiry.dataset.whatsappEnquiry);if(car)sendEnquiry(car,null);}
    });
    const form=document.getElementById("detail-enquiry");if(form)form.addEventListener("submit",event=>{event.preventDefault();const car=cars.find(item=>item.id===new URLSearchParams(location.search).get("id"));if(car)sendEnquiry(car,form);});
    window.addEventListener("storage",event=>{if(event.key===SAVED_KEY){updateSavedCounts();renderInventory();renderSavedPage();if(document.getElementById("car-detail-content"))renderDetail();}});
  });
})();