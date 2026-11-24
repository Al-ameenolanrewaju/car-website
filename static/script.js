(() => {
  "use strict";
  const SAVED_KEY = "premier_saved_cars_v1";
  const money = (value,currency="NGN") => { try { return new Intl.NumberFormat("en-NG",{style:"currency",currency,maximumFractionDigits:0}).format(value); } catch (_) { return String(value); } };
  let cars = [];
  let siteSettings = {business_name:"Premier Motorworks",whatsapp_number:""};
  let csrfToken = "";
  const escapeHTML = value => String(value ?? "").replace(/[&<>\"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'\"':"&quot;","'":"&#39;"}[c]));
  function safeVehicle(v) { const x={...v}; for (const k of ["id","slug","make","model","name","currency","mileageUnit","transmission","fuel","condition","body","engine","drive","colour","description","tag","status"]) if(x[k]!==undefined)x[k]=escapeHTML(x[k]); x.features=Array.isArray(x.features)?x.features.map(escapeHTML):[]; x.images=Array.isArray(x.images)?x.images.map(escapeHTML):[]; return x; }
  async function loadVehicles() {
    const grid=document.getElementById("inventory-grid"), count=document.getElementById("result-count");
    try { const r=await fetch("/api/vehicles"); if(!r.ok)throw new Error(); const d=await r.json(); cars=(d.vehicles||[]).map(safeVehicle); if(count)count.textContent=cars.length+ (cars.length===1?" vehicle":" vehicles"); if(!cars.length&&grid)grid.innerHTML='<div class="loading-note">Our collection is being updated. Please check back soon.</div>'; }
    catch (_) { if(count)count.textContent="Inventory unavailable"; if(grid)grid.innerHTML='<div class="loading-note">We could not load the collection right now. Please refresh the page.</div>'; }
    try { const t=await fetch("/api/csrf-token"); if(t.ok)csrfToken=(await t.json()).csrf_token||""; } catch (_) {}
    try { const r=await fetch("/api/site-settings"); if(r.ok)siteSettings={...siteSettings,...await r.json()}; } catch (_) {}
  }
  const readSaved = () => { try { const value=JSON.parse(localStorage.getItem(SAVED_KEY)||"[]"); return Array.isArray(value)?value.filter(id=>cars.some(car=>car.id===id)):[]; } catch (_) { return []; } };
  const writeSaved = ids => { localStorage.setItem(SAVED_KEY,JSON.stringify([...new Set(ids)])); updateSavedCounts(); };
  function updateSavedCounts(){ const count=readSaved().length; document.querySelectorAll("[data-saved-count]").forEach(el=>el.textContent=count); }
  function cardMarkup(car){
    const saved=readSaved().includes(car.id);
    return `<article class="car-card" data-car-id="${car.id}">
      <div class="car-image"><a href="car.html?id=${encodeURIComponent(car.id)}" aria-label="View ${car.name}"><img src="${car.images[0] || "/assets/car-placeholder.svg"}" alt="${car.year} ${car.name}" loading="lazy" decoding="async"></a>
        <span class="car-tag">${car.tag}</span><button class="favorite ${saved?"is-saved":""}" type="button" data-save-car="${car.id}" aria-pressed="${saved}" aria-label="${saved?"Remove":"Save"} ${car.name}">${saved?"♥":"♡"}</button></div>
      <div class="car-info"><p class="car-kicker">${car.year} · ${car.condition==="new"?"Brand new":"Pre-owned"} · ${car.body}</p>
        <h3><a href="car.html?id=${encodeURIComponent(car.id)}">${car.name}</a></h3>
        <p class="car-meta"><span>${car.mileage?car.mileage.toLocaleString()+" "+(car.mileageUnit||"km"):"New"}</span><span>${car.transmission}</span><span>${car.fuel}</span></p>
        <div class="car-bottom"><strong class="car-price">${money(car.price,car.currency)}</strong><a class="car-open" href="car.html?id=${encodeURIComponent(car.id)}">View details <span aria-hidden="true">→</span></a></div></div>
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
      <div class="detail-main-image"><img id="detail-main-image" src="${car.images[0] || "/static/car-placeholder.svg"}" alt="${car.name}" fetchpriority="high"></div>
      ${car.images.slice(0,3).map((src,index)=>`<button class="detail-thumb ${index===0?"is-active":""}" type="button" data-gallery-src="${src}" aria-label="Show vehicle image ${index+1}"><img src="${src}" alt="" loading="lazy" decoding="async"></button>`).join("")}
    </div><section class="detail-info"><p class="eyebrow">${car.year} · ${car.condition==="new"?"Brand new":"Pre-owned"} · ${car.body}</p><h1>${car.name}</h1><p class="detail-price">${money(car.price,car.currency)}</p><p class="detail-description">${car.description}</p>
      <div class="detail-specs">
        <div class="spec-item"><span>Year</span><strong>${car.year}</strong></div><div class="spec-item"><span>Mileage</span><strong>${car.mileage?car.mileage.toLocaleString()+" "+(car.mileageUnit||"km"):"Brand new"}</strong></div>
        <div class="spec-item"><span>Transmission</span><strong>${car.transmission}</strong></div><div class="spec-item"><span>Fuel type</span><strong>${car.fuel}</strong></div>
        <div class="spec-item"><span>Body type</span><strong>${car.body}</strong></div><div class="spec-item"><span>Engine</span><strong>${car.engine}</strong></div>
        <div class="spec-item"><span>Drivetrain</span><strong>${car.drive}</strong></div><div class="spec-item"><span>Exterior</span><strong>${car.colour}</strong></div>
      </div>
      <h2 class="detail-subhead">Features & equipment</h2><div class="feature-list">${car.features.map(item=>`<span>${item}</span>`).join("")}</div>
      <div class="seller-panel"><strong>Premier Motorworks</strong><p>Vehicle enquiries are handled by our sales team. Ask us about availability, viewing arrangements and the next steps.</p></div>
      <div class="detail-actions"><button class="button button-gold" type="button" data-whatsapp-enquiry="${car.id}">Enquire on WhatsApp ↗</button><button class="button button-outline" type="button" data-save-car="${car.id}" aria-pressed="${saved}">${saved?"♥ Saved":"♡ Save for later"}</button></div>
      <form class="detail-enquiry" id="detail-enquiry"><h2>Ask about this vehicle</h2><p>Send a secure enquiry directly to our team. Your message will be saved for follow-up.</p><div class="enquiry-form"><input name="name" autocomplete="name" placeholder="Your name" required maxlength="120"><input name="email" type="email" autocomplete="email" placeholder="Your email address" required maxlength="255"><input name="phone" type="tel" autocomplete="tel" placeholder="Your phone number" required maxlength="40"><textarea name="message" placeholder="What would you like to know?" maxlength="5000" required></textarea><input name="website" tabindex="-1" autocomplete="off" aria-hidden="true" class="form-honeypot"><button class="button button-gold" type="submit">Send enquiry ↗</button><p class="enquiry-feedback" aria-live="polite"></p></div></form>
    </section>`;
    const related=cars.filter(item=>item.id!==car.id&&(item.make===car.make||item.body===car.body));
    let similar=document.getElementById("similar-section");
    if(!similar){similar=document.createElement("section");similar.className="similar-section";similar.id="similar-section";root.insertAdjacentElement("afterend",similar);}
    similar.hidden=related.length===0;
    similar.innerHTML=related.length?'<div class="section-heading"><div><p class="eyebrow">Keep exploring</p><h2>Similar <em>vehicles.</em></h2></div></div><div class="inventory-grid">'+related.map(cardMarkup).join("")+'</div>':"";
  }
  function sendEnquiry(car,form){
    let name="",phone="",message="";
    if(form){const data=new FormData(form);name=String(data.get("name")||"").trim();phone=String(data.get("phone")||"").trim();message=String(data.get("message")||"").trim();}
    const body=[`Hello Premier Motorworks, I'm interested in the ${car.year} ${car.name} (${money(car.price)}).`,name?`Name: ${name}`:"",phone?`Phone: ${phone}`:"",message?`Message: ${message}`:"Please share availability and viewing details."].filter(Boolean).join("\\n");
    const number=String(siteSettings.whatsapp_number||"").replace(/[^0-9]/g,"");
    const url=number?"https://wa.me/"+number+"?text="+encodeURIComponent(body):"https://wa.me/?text="+encodeURIComponent(body);
    window.open(url,"_blank","noopener,noreferrer");
  }
  document.addEventListener("DOMContentLoaded",async()=>{
    updateSavedCounts();
    await loadVehicles();
    populateFilters();renderInventory();renderSavedPage();renderDetail();
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
    const form=document.getElementById("detail-enquiry");if(form)form.addEventListener("submit",async event=>{
      event.preventDefault(); const car=cars.find(item=>item.id===new URLSearchParams(location.search).get("id")); if(!car)return;
      const feedback=form.querySelector(".enquiry-feedback"),button=form.querySelector('button[type="submit"]'),data=new FormData(form);
      const payload={name:data.get("name"),email:data.get("email"),phone:data.get("phone"),message:data.get("message"),website:data.get("website"),vehicle_id:car.id};
      if(feedback)feedback.textContent="Sending your enquiry…"; if(button)button.disabled=true;
      try { const token=csrfToken; const response=await fetch("/api/enquiries",{method:"POST",headers:{"Content-Type":"application/json","X-CSRFToken":token},body:JSON.stringify(payload)}); const result=await response.json(); if(!response.ok)throw new Error(result.error||"Your enquiry could not be sent."); if(feedback)feedback.textContent=result.message||"Thank you. Your enquiry has been received."; form.reset(); }
      catch(error){if(feedback)feedback.textContent=error.message||"Please try again.";} finally{if(button)button.disabled=false;}
    });
    window.addEventListener("storage",event=>{if(event.key===SAVED_KEY){updateSavedCounts();renderInventory();renderSavedPage();if(document.getElementById("car-detail-content"))renderDetail();}});
  });
})();