OUTDIR=build
INDIR=public_dl2
DATADIR=data
URL=https://zenodo.org/record/7298569/files/


all: \
	${OUTDIR}/gamma_test.dl2.h5 \
	${OUTDIR}/proton_test.dl2.h5 \

gammas_train_en = $(shell seq -f %02.0f 0 10)
gammas_train_clf = $(shell seq -f %02.0f 11 22)
gammas_test = $(shell seq -f %02.0f 23 42)
protons_train = $(shell seq -f %02.0f 0 4)
protons_test = $(shell seq -f %02.0f 5 19)

gamma_train_en_files = $(addprefix ${INDIR}/gamma-diffuse_with_images_, $(addsuffix .dl2.h5, ${gammas_train_en}))
gamma_train_clf_files = $(addprefix ${INDIR}/gamma-diffuse_with_images_, $(addsuffix .dl2.h5, ${gammas_train_clf}))
gamma_test_files = $(addprefix ${INDIR}/gamma-diffuse_with_images_, $(addsuffix .dl2.h5, ${gammas_test}))
proton_train_files = $(addprefix ${INDIR}/proton_with_images_, $(addsuffix .dl2.h5, ${protons_train}))
proton_test_files = $(addprefix ${INDIR}/proton_with_images_, $(addsuffix .dl2.h5, ${protons_test}))

download: ${gamma_files} ${proton_files}
merge: ${DATADIR}/gamma_test.dl2.h5 ${DATADIR}/gamma_train_en.dl2.h5 ${DATADIR}/gamma_train_clf.dl2.h5 ${DATADIR}/proton_train.dl2.h5 ${DATADIR}/proton_test.dl2.h5

${INDIR}/%.dl2.h5 : | ${INDIR}
	curl -fLo $@ ${URL}/$*.dl2.h5?download=1


${DATADIR}/gamma_train_en.dl2.h5: ${gamma_train_en_files} | ${DATADIR}
	ctapipe-merge \
		--no-dl1-images \
		--no-true-images \
		--progress \
		--provenance-log=$@.provlog \
		--log-file=$@.log \
		--log-level=INFO \
		--overwrite \
		-o $@ \
		${gamma_train_en_files}

${DATADIR}/gamma_train_clf.dl2.h5: ${gamma_train_clf_files} | ${DATADIR}
	ctapipe-merge \
		--no-dl1-images \
		--no-true-images \
		--progress \
		--provenance-log=$@.provlog \
		--log-file=$@.log \
		--log-level=INFO \
		--overwrite \
		-o $@ \
		${gamma_train_clf_files}

${DATADIR}/gamma_test.dl2.h5: ${gamma_test_files} | ${DATADIR}
	ctapipe-merge \
		--no-dl1-images \
		--no-true-images \
		--progress \
		--provenance-log=$@.provlog \
		--log-file=$@.log \
		--log-level=INFO \
		--overwrite \
		-o $@ \
		${gamma_test_files}

${DATADIR}/proton_train.dl2.h5: ${proton_train_files} | ${DATADIR}
	echo ${proton_train_files}
	ctapipe-merge \
		--no-dl1-images \
		--no-true-images \
		--progress \
		--provenance-log=$@.provlog \
		--log-file=$@.log \
		--log-level=INFO \
		--overwrite \
		-o $@ \
		${proton_train_files}

${DATADIR}/proton_test.dl2.h5: ${proton_test_files} | ${DATADIR}
	ctapipe-merge \
		--no-dl1-images \
		--no-true-images \
		--progress \
		--provenance-log=$@.provlog \
		--log-file=$@.log \
		--log-level=INFO \
		--overwrite \
		-o $@ \
		${proton_test_files}


${OUTDIR}/%_test.dl2.h5: ${DATADIR}/%_test.dl2.h5 ${OUTDIR}/energy.pkl ${OUTDIR}/classifier.pkl config/apply_config.yml
	ctapipe-apply-models \
		-i $< -o $@ \
		--reconstructor ${OUTDIR}/energy.pkl \
		--reconstructor ${OUTDIR}/classifier.pkl \
		-c config/apply_config.yml \
		--overwrite \
		--provenance-log=$@.provlog \
		--log-file=${OUTDIR}/apply_$*.log \
		--log-level=INFO


${OUTDIR}/energy.pkl: ${DATADIR}/gamma_train_en.dl2.h5  config/train_energy_regressor.yml | ${OUTDIR}
	ctapipe-train-energy-regressor \
		-i $< --output=$@ \
		-c config/train_energy_regressor.yml \
		--provenance-log=$@.provlog \
		--log-file=${OUTDIR}/train_energy.log \
		--log-level=INFO \
		--overwrite

${OUTDIR}/classifier.pkl: ${OUTDIR}/proton_train.dl2.h5 ${OUTDIR}/gamma_train_clf.dl2.h5  config/train_particle_classifier.yml
	ctapipe-train-particle-classifier \
		-o $@ \
		--signal ${OUTDIR}/gamma_train_clf.dl2.h5 \
		--background ${OUTDIR}/proton_train.dl2.h5 \
		-c config/train_particle_classifier.yml \
		--provenance-log=$@.provlog \
		--log-file=${OUTDIR}/train_classifier.log \
		--log-level=INFO \
		--overwrite

${OUTDIR}/gamma_train_clf.dl2.h5: data/gamma_train_clf.dl2.h5 ${OUTDIR}/energy.pkl config/apply_config.yml
	ctapipe-apply-models \
		-i $< -o $@ \
		--reconstructor ${OUTDIR}/energy.pkl \
		-c config/apply_config.yml \
		--overwrite \
		--provenance-log=$@.provlog \
		--log-file=${OUTDIR}/apply_gamma_train_clf.log \
		--log-level=INFO

${OUTDIR}/proton_train.dl2.h5: data/proton_train.dl2.h5 ${OUTDIR}/energy.pkl
	ctapipe-apply-models \
		-i $< -o $@ \
		--reconstructor ${OUTDIR}/energy.pkl \
		-c config/apply_config.yml \
		--overwrite \
		--provenance-log=$@.provlog \
		--log-file=${OUTDIR}/apply_proton_train.log \
		--log-level=INFO


${OUTDIR}:
	mkdir -p $@

${INDIR}:
	mkdir -p $@

${DATADIR}:
	mkdir -p $@


clean:
	rm -rf ${OUTDIR}

.PHONY: all clean
.DELETE_ON_ERROR:
