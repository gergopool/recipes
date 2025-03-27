document.addEventListener('DOMContentLoaded', function() {
    // Add ingredient row - check if element exists first
    const addIngredientBtn = document.getElementById('add-ingredient');
    if (addIngredientBtn) {
        addIngredientBtn.addEventListener('click', function() {
            const container = document.getElementById('ingredients-container');
            const count = container.querySelectorAll('.ingredient-row').length;
            
            const newRow = document.createElement('div');
            newRow.className = 'ingredient-row mb-3';
            newRow.innerHTML = `
                <div class="row g-2">
                    <div class="col-md-5">
                        <input type="text" class="form-control" name="ingredient_name" placeholder="${window.siteTranslations.ingredient_name}" required>
                    </div>
                    <div class="col-md-3">
                        <input type="text" class="form-control" name="ingredient_amount" placeholder="${window.siteTranslations.amount}">
                    </div>
                    <div class="col-md-3">
                        <select class="form-select" name="ingredient_unit">
                            <option value="">${window.siteTranslations.select_unit}</option>
                            <option value="g">${window.siteTranslations.unit_g}</option>
                            <option value="dkg">${window.siteTranslations.unit_dkg}</option>
                            <option value="pcs">${window.siteTranslations.unit_pcs}</option>
                            <option value="coffee_spoon">${window.siteTranslations.unit_coffee_spoon}</option>
                            <option value="teaspoon">${window.siteTranslations.unit_teaspoon}</option>
                            <option value="tablespoon">${window.siteTranslations.unit_tablespoon}</option>
                            <option value="ml">${window.siteTranslations.unit_ml}</option>
                            <option value="liter">${window.siteTranslations.unit_liter}</option>
                            <option value="pinch">${window.siteTranslations.unit_pinch}</option>
                            <option value="little">${window.siteTranslations.unit_little}</option>
                            <option value="lot">${window.siteTranslations.unit_lot}</option>
                        </select>
                    </div>
                    <div class="col-md-1">
                        <button type="button" class="btn btn-danger remove-ingredient">-</button>
                    </div>
                </div>
            `;
            
            container.appendChild(newRow);
            
            // Add event listener to the new remove button
            const removeBtn = newRow.querySelector('.remove-ingredient');
            removeBtn.addEventListener('click', function() {
                this.closest('.ingredient-row').remove();
            });
        });
    }
    
    // Add step row
    const addStepBtn = document.getElementById('add-step');
    if (addStepBtn) {
        addStepBtn.addEventListener('click', function() {
            const container = document.getElementById('steps-container');
            const count = container.querySelectorAll('.step-row').length;
            
            const newRow = document.createElement('div');
            newRow.className = 'step-row mb-3';
            newRow.innerHTML = `
                <div class="row">
                    <div class="col-md-8">
                        <textarea class="form-control" name="step_description_${count}" rows="3" placeholder="${window.siteTranslations.step_description}" required></textarea>
                    </div>
                    <div class="col-md-4">
                        <label class="form-label">${window.siteTranslations.step_image}</label>
                        <div class="custom-file-input">
                            <input class="form-control" type="file" name="step_image_${count}" accept="image/*">
                            <label class="custom-file-label">
                                <i class="bi bi-image"></i> Kép feltöltése
                            </label>
                        </div>
                    </div>
                </div>
            `;
            
            container.appendChild(newRow);
        });
    }
    
    // Remove ingredient row
    document.querySelectorAll('.remove-ingredient').forEach(button => {
        button.addEventListener('click', function() {
            this.closest('.ingredient-row').remove();
        });
    });
    
    // Recipe card click handlers
    document.querySelectorAll('.recipe-card').forEach(card => {
        card.addEventListener('click', () => {
            window.location = card.dataset.recipeUrl;
        });
    });
    
    // Custom file input handling
    document.querySelectorAll('.custom-file-input input[type="file"]').forEach(input => {
        // Update label text with filename when file is selected
        input.addEventListener('change', function() {
            const label = this.nextElementSibling;
            if (this.files.length > 0) {
                label.textContent = this.files[0].name;
            } else {
                label.innerHTML = '<i class="bi bi-image"></i> Kép feltöltése';
            }
        });
    });
});